# Odoo2OTRS

This script is used to interconnect the Odoo system to OTRS, making customers able to use the ticketing system.
It works in this way:
 - Check if in Odoo DB there are new companies added
 - If the company's comment contains otrs
 - If yes, it clone the company into OTRS database and create a user based on the email insert into odoo 
 - Will send an email to the customer with generated password and email
 
The script has been wrote in python.
NOTE: You must run it as root (root cron). Remember also to configure it correctly before use.

To Do:
- Disable auto commit of queries and activate it and do it at the end of the program. (Avoiding inserting errors)
- Make it executable also as a user, not only as root
- Optimize
