from fastapi import FastAPI, File, UploadFile
import xmltodict
import pandas as pd
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.post("/convert-xml-to-xlsx/")
async def convert_xml_to_xlsx(file: UploadFile = File(...)):
    # Parse XML content
    content = await file.read()
    data_dict = xmltodict.parse(content)
    
    # open vouchers list
    vouchers = data_dict['ENVELOPE']['BODY']['IMPORTDATA']['REQUESTDATA']['TALLYMESSAGE']
    
    # Prepare a list to store all voucher data
    voucher_data = []
    
    # filter for Receipt 
    for voucher in vouchers:
        voucher_details = voucher.get('VOUCHER', {})
        if voucher_details.get('VOUCHERTYPENAME') == 'Receipt':
            voucher_entry = {}

            # Extract all available fields 
            for key, value in voucher_details.items():
                if isinstance(value, str):  
                    voucher_entry[key] = value

            # Remove ledger items from ALLLEDGERENTRIES.LIST.
            ledger_entries = voucher_details.get('ALLLEDGERENTRIES.LIST', [])
            if not isinstance(ledger_entries, list):
                ledger_entries = [ledger_entries]
            for entry in ledger_entries:
                ledger_name = entry.get('LEDGERNAME', '')
                amount = entry.get('AMOUNT', '')
                
                if ledger_name and amount:
                    # Add ledger-specific data
                    voucher_entry.update({
                        'LEDGERNAME': ledger_name,
                        'AMOUNT': amount,
                    })
            
            # Append voucher data with ledger entries
            voucher_data.append(voucher_entry)
    
    # Convert to DataFrame
    df = pd.DataFrame(voucher_data)
    
    # Save to XLSX
    xlsx_file_path = "output.xlsx"
    df.to_excel(xlsx_file_path, index=False)
    
    # Return the XLSX file for download
    return FileResponse(xlsx_file_path, filename="output.xlsx")
