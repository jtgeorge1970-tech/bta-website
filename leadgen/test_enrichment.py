from apollo_enrichment import search_request, choose_decision_maker, enrichment_request, apply_enrichment
from enrichment_queue import build

def run_tests():
    lead={"company_id":"1","company_name":"Example Imports","domain":"https://example.com/path","qualification_status":"QUALIFIED","qualification_score":88,"qualification_tier":"A"}
    req=search_request(lead)
    assert req["q_organization_domains_list"]==["example.com"] and "chief financial officer" in req["person_titles"]
    people=[{"id":"bbbbbbbbbbbbbbbbbbbbbbbb","name":"Finance Director","title":"Director of Finance","seniority":"director"},{"id":"aaaaaaaaaaaaaaaaaaaaaaaa","name":"Company Owner","title":"Owner","seniority":"owner"}]
    pick=choose_decision_maker(people); assert pick["name"]=="Company Owner"
    enrich=enrichment_request(pick); assert enrich["id"]=="aaaaaaaaaaaaaaaaaaaaaaaa" and enrich["reveal_phone_number"] is True
    merged=apply_enrichment(lead,{**pick,"email":"owner@example.com"},"2125551234")
    assert merged["contact_name"]=="Company Owner" and merged["email_source"]=="Apollo" and merged["phone_source"]=="Apollo"
    q=build([lead,{**lead,"company_id":"2","qualification_status":"RESEARCH"}]); assert len(q)==1 and q[0]["enrichment_status"]=="PENDING_SEARCH"
    print("PASS: Apollo decision-maker enrichment workflow")
if __name__=="__main__": run_tests()
