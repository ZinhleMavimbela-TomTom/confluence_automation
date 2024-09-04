from bs4 import BeautifulSoup
import re
import csv
import os
import mysql.connector 
import fnmatch
from cgitb import html
from atlassian import Confluence
import mysql.connector
import json
import requests
from requests.auth import HTTPBasicAuth

region =str(os.getenv("regions"))
version =str(os.getenv("version"))
remove_keyword= str(os.getenv("Remove_Word"))
change_from = str(os.getenv("Change_parameter1"))
change_to = str(os.getenv("Change_parameter2"))
space_name="~"+str(os.getenv("space"))
title_name=str(os.getenv("title"))
csvfilepath = 'country_name.csv'
# local container for country name and description
country_isocode_description = []

# list to store unmatched country codes
unmatched_countries = []

htmlstring = ""

# class CountryData is to hold the name, the ISO code, and the description of each country found in the HTML file
class CountryData:
    def __init__(self, name, data_ver, code, description):
        self.name = name
        self.data_ver = data_ver
        self.code = code
        self.description = description

    # printing helper
    def __str__(self):
        return "country name: %s, country ISO code: %s, \ndescription: %s" % (self.data_ver, self.name, self.code, self.description)
def region_convert():

    if region == "cas":
        return "Central Asia"
    if region == "eur":
        return "Europe"
    if region == "nam":
        return "North America"
    if region == "oce":
        return "Oceania"
    if region == "sea":
        return "Southeast Asia"
    if region == "mea":
        return "Middle East Africa"
    if region == "isr":
        return "Israel"
    if region == "lam":
        return "Latin America"
    if region == "s_o":
        return "Pacific Ocean"
    if region == "ind":
        return "India"
    if region == "kor":
        return "Korea"
    
def format_html_body(c_code, descript):
    htmlstring = htmlstring +"<h5>{}</h5>{}".format(c_code,descript)

# function to match the country name with the ISO code from the country_names csv file
def matching_country_code(name):
    with open(csvfilepath, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)
        for row in datareader:
            if row[1] == name:
                return row[0]
            else:
                if re.search(row[1], name):
                    return row[0]

# function to match the country name with the ISO code from the country_names csv file
def matching_country_code(name):
    with open(csvfilepath, 'r') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader)
        for row in datareader:
            if row[1] == name:
                return row[0]
            else:
                if re.search(row[1], name):
                    return row[0]

# main function to read the HTML file and parse through and extract the country name and the country description
def pulling_data():
    file_list = f'/share/nds-sources/products/commercial/{region}{version}/documentation/mn/release_notes/release_notes/whats_new/'
    pattern = f'highlights_and_improvements_mn_{region}_{version}.html'
    
    with open(os.path.join(file_list, pattern), 'r') as html_file:
            content = html_file.read()
            soup = BeautifulSoup(content, 'html.parser')
            # get the data source version from the html title
            title_string = (soup.find('title'))
            data_source_version = ((title_string.text).split()[2])

            # country names have the h2 tag in the HTML file
            country_name_tags = soup.find_all("h2", {"class": "CountryName"})
            country_names = []
            # remove extra spaces from the country names
            for c in country_name_tags:
                sanitize = re.sub(r"[\n\t]*", "", c.text)
                sanitize = re.sub(' +', " ", sanitize)
                country_names.append(sanitize)

            # descriptions have the ul tag in the HTML file
            description_tags = soup.find_all("ul", {"class": "CountryRemark"})
            descriptions = []
            for d in description_tags:
                result = d.find_all("li")
                country_descrip = []
                for li in result:
                    # fix random newlines, tabs, spaces in strings
                    sanitize = u''.join(li.findAll(text=True))
                    sanitize = re.sub(r"[\n\t]*", "", sanitize)
                    sanitize = re.sub(' +', " ", sanitize)
                    sanitize =re.sub('\xa0',"", sanitize)
                    sanitize =re.sub('&nbsp;',"", sanitize)
                    sanitize = re.sub('&amp;', "and", sanitize)
                    sanitize = re.sub('&', "and", sanitize)
                    if ((len(remove_keyword))!=0):
                        split_remove =remove_keyword.split(",")
                        for i in range(len(split_remove)):
                            sanitize=re.sub(split_remove[i], "",sanitize)
                    if ((len(change_from)!=0) and (len(change_to)!=0)):
                        #splits the change parameter 1 and change parameter 2 if there are multiple parameters 
                        split_change_to = change_to.split(",")
                        split_change_from = change_from.split(",")
                        #loops through the str array with divided words and does replacement by mapping the words 
                        #for example "Approximately" updated to "change" therefore split_change_to[0] maps to split_change_to[0]
                        for m,j in zip(range(len(split_change_to)),range(len(split_change_from))):
                            sanitize=re.sub(split_change_from[m],split_change_to[j],sanitize)
                    sanitize = sanitize.strip()
                    country_descrip.append(sanitize)
                descriptions.append(country_descrip)
                del country_descrip
             # in case, General is added as a country name
            if country_names[0] == "General":
                country_names = country_names[1:]
                descriptions = descriptions[1:]
            # find the ISO codes based on the country name
            iso_codes = []
            for country_name in country_names:
                iso = matching_country_code(country_name)
                iso_codes.append(iso)
                if iso is None:
                    unmatched_countries.append(country_name)

             # order matters, so first error checking is to make sure there is a 1:1:1 correlation between all individual lists
            if(len(country_names) == len(iso_codes) == len(descriptions)):
                for i in range(len(country_names)):
                    # combine all information into the class
                    country_isocode_description.append(CountryData(
                        country_names[i], data_source_version, iso_codes[i], descriptions[i]))
            else:
                print("Error sizes do not match")
    
def print_all():
    # print to check
    print("____________________________________________________________________________________________________________________________________")
    for entry in country_isocode_description:
        print("__________________________________________________________________________________________________________________________________")
        print(entry.name, "(", entry.code, ")-", entry.data_ver, "\n", entry.description)

def preparing_data():
    count=0
    for country in country_isocode_description:
        one_country_description_as_string = ""
        
        for single in country.description:
            single="<li>"+ single+ "</li>"
            one_country_description_as_string = one_country_description_as_string + single
            one_country_description_as_string = one_country_description_as_string+ "\n"
        if count==0:
            assign_region=region_convert()
            country.name ="<h3>"+assign_region+"</h3><br></br>"+"<h5>"+country.name+"</h5>"
        #print to check what is being sent to confluence
        print(country.data_ver + " " + country.name + " " + one_country_description_as_string)
        format_html_body(country.name, one_country_description_as_string)
        count=count+1
        one_country_description_as_string = ""

def pushing_data():
    #region change to fullname
    url = "https://tomtom.atlassian.net/wiki/api/v2/pages/217024057"
    
    auth = HTTPBasicAuth(
    str(os.getenv("user_name")), 
    str(os.getenv("access_token")))    
    
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    
    payload = json.dumps({
    "id": "217024057",
    "status": "current",
    "title": str(os.getenv("space")),
    "body": {
        "representation": "wiki",
        "value": "Hello World"
    },
    "version": {
        "number": 1479,
        "message": htmlstring
    }
    })
    
    response = requests.request(
        "PUT",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

pulling_data()
print("Total Country Count: ", len(country_isocode_description))
print_all()
if (len(unmatched_countries) == 0):
    print("Pushing to Confluence Page")
    preparing_data()
    pushing_data()
    
else:
    print("ERROR: These countries have no match in the csv file, please update csv file firstly and run again: ")
    for unmatch in unmatched_countries:
        print(unmatch)
