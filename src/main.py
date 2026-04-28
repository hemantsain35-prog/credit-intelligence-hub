def run_pipeline():
    logger.info("="*60)
    logger.info("Starting Multi-Source B2B Lead Intelligence Pipeline")
    logger.info("="*60)

    telegram = TelegramService()

    # ✅ FORCE TEST (debug)
    telegram.send_message("🚀 Pipeline started")

    # ============================================================
    # STEP 1: FETCH
    # ============================================================
    try:
        indiamart_items = IndiaMART().fetch_all()
    except:
        indiamart_items = []

    try:
        tradeindia_items = TradeIndia().fetch_all()
    except:
        tradeindia_items = []

    try:
        rss_items = RssScraper().fetch_all()
    except:
        rss_items = []

    all_items = indiamart_items + tradeindia_items + rss_items

    if not all_items:
        telegram.send_message("⚠️ No data fetched from sources")
        return

    # ============================================================
    # STEP 2: DEDUP
    # ============================================================
    unique_items = deduplicate_items(all_items)

    # ============================================================
    # STEP 3: DEMAND
    # ============================================================
    detector = DemandDetector()
    items_with_demand = []

    for item in unique_items:
        demand_info = detector.analyze(item)
        if demand_info["is_demand"]:
            item.update(demand_info)
            items_with_demand.append(item)

    # ============================================================
    # STEP 4: VALUE
    # ============================================================
    high_value_items = [
        item for item in items_with_demand
        if item.get("numeric_value", 0) >= 50
    ]

    # ============================================================
    # STEP 5: LOCATION
    # ============================================================
    location_filter = LocationFilter()

    gurgaon_items = [
        item for item in high_value_items
        if location_filter.is_gurgaon(item.get("title", "")) or
           location_filter.is_gurgaon(item.get("description", "")) or
           location_filter.is_gurgaon(item.get("location", ""))
    ]

    if not gurgaon_items:
        telegram.send_message("⚠️ No Gurgaon leads found")
        return

    # ============================================================
    # STEP 6: CONTACT
    # ============================================================
    contact_extractor = ContactExtractor()

    for item in gurgaon_items:
        full_text = f"{item.get('title', '')} {item.get('description', '')}"
        item.update(contact_extractor.extract(full_text))

    # ============================================================
    # STEP 7: ENRICH
    # ============================================================
    enricher = CompanyEnricher()

    for item in gurgaon_items:
        item.update(enricher.enrich(item))

    # ============================================================
    # STEP 8: SCORE
    # ============================================================
    scorer = LeadScorer()

    for item in gurgaon_items:
        item["score"] = scorer.calculate_score(item)

    # ============================================================
    # STEP 9: FINAL FILTER
    # ============================================================
    qualified_leads = [
        item for item in gurgaon_items
        if item.get("score", 0) >= 5
    ]

    if not qualified_leads:
        telegram.send_message("⚠️ No qualified leads (score filter)")
        return

    # ============================================================
    # STEP 10: RANK
    # ============================================================
    qualified_leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified_leads[:10]

    # ============================================================
    # STEP 11: SAVE
    # ============================================================
    for lead in top_leads:
        lead["id"] = generate_id(lead)
        try:
            send_to_sheet(lead)
        except:
            pass

    # ============================================================
    # STEP 12: TELEGRAM
    # ============================================================
    telegram.send_leads(top_leads)

    logger.info("Pipeline execution complete!")
