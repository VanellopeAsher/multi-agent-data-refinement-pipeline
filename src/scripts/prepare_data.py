import os
import json
import requests
import re
from PyPDF2 import PdfReader


CONFERENCES = [
    "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI",
    "CVPR", "ICCV", "ECCV", "ACL", "KDD"
]

RAW_DIR = "data/raw"
PDF_DIR = "data/pdfs"
PAPERS_JSON = os.path.join(RAW_DIR, "papers.json")


def ensure_dirs():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)


def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_seed_papers():
    papers = []
    for conf in CONFERENCES:
        try:
            src_url = (
                "https://api.openalex.org/sources?"
                f"search={conf}&per-page=1&sort=cited_by_count:desc"
            )
            src_data = fetch_json(src_url)
            src_results = src_data.get("results", [])
            if not src_results:
                continue
            src = src_results[0]
            source_id = src["id"].split("/")[-1]

            works_url = (
                "https://api.openalex.org/works?"
                f"filter=primary_location.source.id:{source_id}"
                "&per-page=1&sort=cited_by_count:desc"
            )
            works_data = fetch_json(works_url)
            items = works_data.get("results", [])
            if items:
                papers.append(items[0])
        except:
            continue
    return papers


def extract_reference_ids(seed_papers):
    ids = set()
    for p in seed_papers:
        refs = p.get("referenced_works", [])
        for rid in refs:
            ids.add(rid)
    return list(ids)


def fetch_reference_papers(ref_ids):
    results = []
    for rid in ref_ids:
        url = f"https://api.openalex.org/works/{rid}"
        try:
            data = fetch_json(url)
            results.append(data)
        except:
            pass
    return results


def save_papers(papers):
    with open(PAPERS_JSON, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)


def load_papers():
    if not os.path.exists(PAPERS_JSON):
        return []
    with open(PAPERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_arxiv_id(meta):
    ids = meta.get("ids") or {}
    url = ids.get("arxiv")
    if not isinstance(url, str):
        return None
    m = re.search(r"arxiv\.org/abs/([^/]+)", url)
    if not m:
        return None
    s = m.group(1)
    s = s.split("v")[0]
    return s


def get_nested(d, path):
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def gather_pdf_urls(meta):
    urls = {}
    aid = extract_arxiv_id(meta)
    if aid:
        urls["arxiv"] = f"https://arxiv.org/pdf/{aid}.pdf"
    u1 = get_nested(meta, ["best_oa_location", "pdf_url"])
    if isinstance(u1, str):
        urls["best_oa_pdf"] = u1
    u2 = get_nested(meta, ["best_oa_location", "url"])
    if isinstance(u2, str):
        urls["best_oa_url"] = u2
    u3 = get_nested(meta, ["open_access", "oa_url"])
    if isinstance(u3, str):
        urls["oa_url"] = u3
    u4 = get_nested(meta, ["primary_location", "landing_page_url"])
    if isinstance(u4, str):
        urls["primary_landing"] = u4
    return urls


def download_pdf(url, name):
    safe = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)[:100]
    path = os.path.join(PDF_DIR, safe + ".pdf")
    if os.path.exists(path):
        return path
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return path
    except:
        return None


def parse_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except:
        return None


def fetch_all_pdfs_and_parse(papers):
    new_list = []
    for meta in papers:
        urls = gather_pdf_urls(meta)
        oid = meta.get("id") or meta.get("openalex_id") or "paper"
        name = oid.split("/")[-1]

        local = None
        if "arxiv" in urls:
            local = download_pdf(urls["arxiv"], "arxiv_" + name)
        if not local and "best_oa_pdf" in urls:
            local = download_pdf(urls["best_oa_pdf"], "bestoa_" + name)
        if not local and "best_oa_url" in urls:
            local = download_pdf(urls["best_oa_url"], "besturl_" + name)
        if not local and "oa_url" in urls:
            local = download_pdf(urls["oa_url"], "oa_" + name)
        if not local and "primary_landing" in urls:
            local = download_pdf(urls["primary_landing"], "landing_" + name)

        if not local:
            continue

        meta["local_pdf_path"] = os.path.abspath(local)

        text = parse_pdf(local)
        if not text:
            continue

        meta["full_text"] = text
        new_list.append(meta)

    return new_list


def main():
    ensure_dirs()

    seeds = fetch_seed_papers()
    ref_ids = extract_reference_ids(seeds)
    refs = fetch_reference_papers(ref_ids)

    all_papers = seeds + refs
    save_papers(all_papers)

    papers = load_papers()
    papers_with_fulltext = fetch_all_pdfs_and_parse(papers)
    save_papers(papers_with_fulltext)

    print("Stage 0 Complete")
    print("Total papers with full text:", len(papers_with_fulltext))


if __name__ == "__main__":
    main()
