### Code

	sampler.py - Code from the Case Study that procedurally samples the kth element from the full dataset.

	audit.py - Based on Case Study code. It audits the data for unexpected values, and defines functions to update certain unexpected values.
	
	data_to_csv.py - Converts XML data to CSV according to the designated schema, utilizing update functions from audit.py as it goes.

### Map Data

	I selected the Seattle, WA metropolitan area. I have lived in Seattle for a few years, and I am interested in learning more about the local area.

	I downloaded my original dataset from Mapzen; however, in the meantime, Mapzen has shut down (https://mapzen.com/blog/shutdown/) and the data is no longer available from that source. I was able to use my database to reverse-engineer (roughly) the same slice via Overpass API:

	sqlite> SELECT min(lat), min(lon), max(lat), max(lon) FROM nodes;
	46.6080004|-123.931|48.5279998|-121.3350001

	http://overpass-api.de/query_form.html

	Overpass API> (node(46.608,-123.931,48.528,-121.335);<;);out meta;

### Resources

	Course resources
	Case study code
	OpenStreetMap documentation (https://wiki.openstreetmap.org/wiki/Main_Page)
	https://www.sqlite.org/lang_select.html
	https://www.tutorialspoint.com/sqlite/sqlite_unions_clause.htm
