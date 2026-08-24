"""Dependency-free tests for tariff qualification and routing logic."""
from datetime import date
from qualify import score
from validate_contacts import audit

TODAY=date(2026,8,24)

def run_tests():
    a=score({"company_name":"High Value","shipments":1200,"last_shipment":"2026-08-01","origin_countries":["China"],"tariff_exposure":True},TODAY)
    assert a["qualification_score"]==100 and a["qualification_tier"]=="A" and a["qualification_status"]=="QUALIFIED"
    b=score({"company_name":"Mid","shipments":60,"last_shipment":"2026-06-01","origin_countries":["China"]},TODAY)
    assert b["qualification_score"]>=50 and b["qualification_status"]=="QUALIFIED"
    c=score({"company_name":"Weak","shipments":2,"last_shipment":"2022-01-01","origin_countries":["Canada"]},TODAY)
    assert c["qualification_status"]=="RESEARCH"
    good=audit({"contact_name":"Jane Doe","phone":"212-555-1234","phone_source":"Apollo","email":"jane@example.com","email_source":"Apollo"})
    assert good["valid"]
    bad=audit({"contact_name":"Jane Doe","phone":"212-555-1234","email":"jane@example.com"})
    assert not bad["valid"] and "unverified_phone" in bad["problems"] and "unverified_email" in bad["problems"]
    print("PASS: qualification scoring and strict contact routing")

if __name__=="__main__": run_tests()
