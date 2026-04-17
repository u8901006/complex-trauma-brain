#!/usr/bin/env python3
"""
Fetch latest complex trauma / dissociation research papers from PubMed E-utilities API.
Targets trauma, dissociation, child maltreatment, and interpersonal violence journals.
"""

import json
import os
import sys
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote_plus

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

JOURNALS = [
    "European Journal of Psychotraumatology",
    "Journal of Traumatic Stress",
    "Psychological Trauma: Theory, Research, Practice, and Policy",
    "Trauma, Violence, & Abuse",
    "Journal of Trauma & Dissociation",
    "European Journal of Trauma & Dissociation",
    "Traumatology",
    "Child Abuse & Neglect",
    "Child Maltreatment",
    "Journal of Child & Adolescent Trauma",
    "Child Abuse Review",
    "Journal of Child Sexual Abuse",
    "Journal of Interpersonal Violence",
    "Journal of Family Violence",
    "Aggression and Violent Behavior",
    "Psychology of Violence",
    "Journal of Aggression, Maltreatment & Trauma",
    "Anxiety, Stress, & Coping",
    "Neurobiology of Stress",
    "Chronic Stress",
    "Development and Psychopathology",
    "Stress and Health",
    "Research on Child and Adolescent Psychopathology",
    "Clinical Psychology Review",
]

SEARCH_QUERIES = [
    '(("Psychological Trauma"[Mesh] OR "Stress Disorders, Post-Traumatic"[Mesh] OR "Dissociative Disorders"[Mesh] OR trauma*[tiab] OR PTSD[tiab] OR CPTSD[tiab] OR "complex PTSD"[tiab] OR dissociation[tiab] OR dissociative[tiab] OR depersonalization[tiab] OR derealization[tiab] OR psychotrauma*[tiab] OR "traumatic stress"[tiab] OR "peritraumatic dissociation"[tiab] OR "dissociative subtype"[tiab] OR "dissociative identity disorder"[tiab] OR DID[tiab] OR "childhood trauma"[tiab] OR maltreatment[tiab] OR "child abuse"[tiab] OR "adverse childhood experiences"[tiab] OR "complex posttraumatic stress disorder"[tiab] OR DESNOS[tiab] OR "developmental trauma"[tiab] OR "chronic interpersonal trauma"[tiab])) NOT ("traumatic brain injury"[tiab] OR TBI[tiab] OR orthopedic[tiab] OR fracture[tiab] OR surgery[tiab] OR "trauma center"[tiab] OR "trauma surgery"[tiab])',
]

HEADERS = {"User-Agent": "ComplexTraumaBrainBot/1.0 (research aggregator)"}


def build_query(days: int = 7) -> str:
    lookback = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    date_part = f'"{lookback}"[Date - Publication] : "3000"[Date - Publication]'
    topic_query = SEARCH_QUERIES[0]
    return f"({topic_query}) AND {date_part}"


def search_papers(query: str, retmax: int = 50) -> list[str]:
    params = (
        f"?db=pubmed&term={quote_plus(query)}&retmax={retmax}&sort=date&retmode=json"
    )
    url = PUBMED_SEARCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[ERROR] PubMed search failed: {e}", file=sys.stderr)
        return []


def fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    ids = ",".join(pmids)
    params = f"?db=pubmed&id={ids}&retmode=xml"
    url = PUBMED_FETCH + params
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=60) as resp:
            xml_data = resp.read().decode()
    except Exception as e:
        print(f"[ERROR] PubMed fetch failed: {e}", file=sys.stderr)
        return []

    papers = []
    try:
        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            art = medline.find(".//Article") if medline else None
            if art is None:
                continue

            title_el = art.find(".//ArticleTitle")
            title = (
                (title_el.text or "").strip()
                if title_el is not None and title_el.text
                else ""
            )

            abstract_parts = []
            for abs_el in art.findall(".//Abstract/AbstractText"):
                label = abs_el.get("Label", "")
                text = "".join(abs_el.itertext()).strip()
                if label and text:
                    abstract_parts.append(f"{label}: {text}")
                elif text:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)[:2000]

            journal_el = art.find(".//Journal/Title")
            journal = (
                (journal_el.text or "").strip()
                if journal_el is not None and journal_el.text
                else ""
            )

            pub_date = art.find(".//PubDate")
            date_str = ""
            if pub_date is not None:
                year = pub_date.findtext("Year", "")
                month = pub_date.findtext("Month", "")
                day = pub_date.findtext("Day", "")
                parts = [p for p in [year, month, day] if p]
                date_str = " ".join(parts)

            pmid_el = medline.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            keywords = []
            for kw in medline.findall(".//KeywordList/Keyword"):
                if kw.text:
                    keywords.append(kw.text.strip())

            papers.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "date": date_str,
                    "abstract": abstract,
                    "url": link,
                    "keywords": keywords,
                }
            )
    except ET.ParseError as e:
        print(f"[ERROR] XML parse failed: {e}", file=sys.stderr)

    return papers


def load_reported_pmids(seen_file: str, keep_days: int = 7) -> set[str]:
    if not os.path.exists(seen_file):
        return set()
    try:
        with open(seen_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return set()
    cutoff = (
        datetime.now(timezone(timedelta(hours=8))) - timedelta(days=keep_days)
    ).strftime("%Y-%m-%d")
    pmids = set()
    for date_key, id_list in data.items():
        if date_key >= cutoff:
            pmids.update(id_list)
    return pmids


def save_reported_pmids(
    seen_file: str, date_str: str, new_pmids: list[str], keep_days: int = 7
):
    data = {}
    if os.path.exists(seen_file):
        try:
            with open(seen_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    cutoff = (
        datetime.now(timezone(timedelta(hours=8))) - timedelta(days=keep_days)
    ).strftime("%Y-%m-%d")
    data = {k: v for k, v in data.items() if k >= cutoff}
    data[date_str] = new_pmids
    os.makedirs(os.path.dirname(seen_file) or ".", exist_ok=True)
    with open(seen_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch complex trauma papers from PubMed"
    )
    parser.add_argument("--days", type=int, default=7, help="Lookback days")
    parser.add_argument(
        "--max-papers", type=int, default=50, help="Max papers to fetch"
    )
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--seen", default="", help="Reported PMIDs JSON file for dedup")
    args = parser.parse_args()

    query = build_query(days=args.days)
    print(
        f"[INFO] Searching PubMed for complex trauma papers from last {args.days} days...",
        file=sys.stderr,
    )

    pmids = search_papers(query, retmax=args.max_papers)
    print(f"[INFO] Found {len(pmids)} papers from PubMed", file=sys.stderr)

    reported = load_reported_pmids(args.seen) if args.seen else set()
    if reported:
        before = len(pmids)
        pmids = [p for p in pmids if p not in reported]
        print(
            f"[INFO] Dedup: {before} -> {len(pmids)} (removed {before - len(pmids)} already reported)",
            file=sys.stderr,
        )

    if not pmids:
        print("NO_CONTENT", file=sys.stderr)
        if args.json:
            print(
                json.dumps(
                    {
                        "date": datetime.now(timezone(timedelta(hours=8))).strftime(
                            "%Y-%m-%d"
                        ),
                        "count": 0,
                        "papers": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    papers = fetch_details(pmids)
    print(f"[INFO] Fetched details for {len(papers)} papers", file=sys.stderr)

    if args.seen:
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        save_reported_pmids(
            args.seen, today, [p["pmid"] for p in papers if p.get("pmid")]
        )
        print(f"[INFO] Updated reported PMIDs file: {args.seen}", file=sys.stderr)

    output_data = {
        "date": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
        "count": len(papers),
        "papers": papers,
    }

    out_str = json.dumps(output_data, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(out_str)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"[INFO] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
