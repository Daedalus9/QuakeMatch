import datetime

base_url = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=7000&start={}&end={}"

start_date = datetime.datetime(1998, 7, 19)
end_date = datetime.datetime(2023, 7, 19)

current_date = start_date
links = []

i=0
while current_date <= end_date:
    start_time = current_date.strftime("%Y-%m-%dT%H:%M:%S.0")
    end_time = (current_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.0")
    link = base_url.format(start_time, end_time)
    links.append(link)
    current_date += datetime.timedelta(days=1)
    i=i+1

with open("./logstash/seismic_portal_links.txt", "w") as file:
    for link in links:
        file.write(link + "\n")


        