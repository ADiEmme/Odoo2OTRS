# Odoo2OTRS

This script is used to interconnect the Odoo system to OTRS, making customers able to use the ticketing system.
It works in this way:
 - Check if in Odoo DB there are new companies added
 - If the company's comment contains otrs
 - If yes, it clone the company into OTRS database and create a user based on the email insert into odoo 
 - Will send an email to the customer with generated password and email
 
The script has been wrote in python.
