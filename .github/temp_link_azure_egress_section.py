from pathlib import Path

p = Path('09-07-26_Azure_Firewall_Insertion_Summary.md')
s = p.read_text()
old = '''## 11. Internet egress through a customer-managed firewall

### Azure Firewall
'''
new = '''## 11. Internet egress through a customer-managed firewall

This section is the Internet-egress application of the two customer-managed hub patterns described earlier:

- [Azure Firewall in a Customer-Managed Hub VNet — Method 1](09-05-26-18-55_Azure_Firewall_Customer_Managed_Hub_VNet_Method_1_Deep_Dive.md)
- [Third-Party NGFW/NVA in a Customer-Managed Hub VNet — Method 2](09-05-26-19-45_Third_Party_NGFW_NVA_Customer_Managed_Hub_VNet_Method_2_Deep_Dive.md)

### Azure Firewall
'''
if old not in s:
    raise SystemExit('Section 11 anchor not found')
s = s.replace(old, new, 1)
old2 = '''**Memorize:**

> Traditional Azure egress = default route to the security next hop.

---
'''
new2 = '''**Memorize:**

> Traditional Azure egress = default route to the security next hop.

**Deep dives:**

- [Azure Firewall in a Customer-Managed Hub VNet — Method 1](09-05-26-18-55_Azure_Firewall_Customer_Managed_Hub_VNet_Method_1_Deep_Dive.md)
- [Third-Party NGFW/NVA in a Customer-Managed Hub VNet — Method 2](09-05-26-19-45_Third_Party_NGFW_NVA_Customer_Managed_Hub_VNet_Method_2_Deep_Dive.md)

---
'''
if old2 not in s:
    raise SystemExit('Section 11 footer anchor not found')
s = s.replace(old2, new2, 1)
p.write_text(s)
