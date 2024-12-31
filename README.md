# EarlyAmericanSenateData
This repository contains data related to early American Senate activities, focused on votes on committee participants from the  1<sup>st</sup> to 15<sup>th</sup> Congresses (not including the 12<sup>th</sup>). The data come from voting rolls in the National Archives and the [*Biographical Directory of the United States Congress*](https://bioguide.congress.gov/). This project has been devoted to digitizing and partially cleaning notes made by Dr. Terri Halperin from these primary sources for use in research and analysis.

## 📜 Overview

This first part contains the main information about how we put all this information together. [Skip this and read about how to look at and use the data here](#look-at-the-data)
    
### Where is the data from and how did this come together?
- **Source**: The main data originates from historical records of the United States Senate. These records document committee votes, attendance, and dates from all Congresses from the 1<sup>st</sup> to 15<sup>th</sup> except for the 12<sup>th</sup>. Biographical data (including state, age, party, etc.) come from the [*Biographical Directory of the United States Congress*](https://bioguide.congress.gov/)
- Notes on the data can be found in the [`notes.txt` file](https://github.com/ewolman/EarlyAmericanSenateData/blob/main/notes.txt)

- **Format**: The main raw data and tables generated for the database are in the `Data` folder. 
    - **`scans_and_text`** - The raw data - scanned images of notes and text files containing the raw text from the notes
         - The text files were created using the python package [pytesseract](https://pypi.org/project/pytesseract/) to turn the scans into text files, which in turn could be formed into a dataset (`process_scans.py`)
         - The files are split up into folders by congress. You can see the scans, the unedited text files, and the edited text files. The text needed to be in a specific format to be processed by the `process_text.py` file, ([*see below*](#how-i-parsed-the-text-files)), so each text had to be edited and checked for mistakes since the *pytesseract* package is not mistake-free. However, using this tool is much faster than transcribing all the scanned files.
    - **`vote_data`** - The end product of `process_text.py`, which turns the text from each page into a table, which lists the number of votes each Senator receives, for each committee. They also include the congres, date of committee, and page number from the notes. The files in the `updated` folder have corrected names (for any misspellings which weren't caught or spelling differences updated to match the Congressional Database).
    - **`Merged_Data`** - The end product of `comb_data.py`. These are the csv files from `vote_data` merged with biographical data (`Info.csv`). These sheets contain all congresses up to the congress in the file name and contain the same columns from `vote_data` plus more in-depth biographical data including state, party, age, full name, etc.
    - **Other files** - These are files used to store any name changes that needed to be made due to spelling errors or people with same last name. These are for efficiency so any name changes did not need to be added repeatedly. There is also the biographical data.

- The `database.db` file is a SQL database containing 4 tables:
  - `tSenator` - Each Senator by their corresponding *bioguide.gov* ID and name
  - `tSenatorByCongress` - Each Senator by Congress. They are identified by their *bioguide.gov* ID (`senator_id`) and a new id for each congress they appear in (`senator_congress_id`)
  - `tCommittee` - Each committee, given an id and the date, congress, and page for that committee
  - `tVotes` - The number of votes each Senator received for each committee. The senators are identified by `senator_congress_id` and the committees are identified by `committee_id`.
  - These tables show the smallest amount of information possible to identify each observation and was more for me personally to refresh my SQL skills. The best way to look at the data is from the `useful_tables` folder.
- If you notice errors or have suggestions for improvement, feel free to submit a pull request or open an issue

### Look at the Data
- The `useful_tables` and `visualizations` folders contain tables and graphs to help understand the data.
   - `useful_tables`:
     -  `IndividualVotesByCmte.csv` - The number of votes each senator received for each committee across all congresses
     -  `TotalVotesAllTime.csv` - Information on the number of votes each senator received over their full time in congress
     -  `TotalVotesByCongress.csv` - Information on the number of votes each senator received during each individual congress
     -  `TotalVotesByCongress_FullTerm.csv` - Same as above, but only those who served in more than 3 congresses (if continuous, this would be a full term)
     -  `VotesByParty.csv` - The number of votes that the members of each party received by Congress
     -  `VotesByPartyByYear.csv` - Same as above but split up by year instead of Congress
     -  `tCommittee.csv` - All committees and their pertinent information (date, congress, page)
- [**Tableau Dashboard** - A Tableau Public Dashboard where you can compare Senators based on the votes they received in each Congress.](https://public.tableau.com/app/profile/elias.wolman/viz/SenatorDashboard/Dashboard1?publish=yes)
## How I parsed the text files

The `process_text.py` file is the main part of this project. It processes each text file for a given congress, creating tables of each senator's votes by committee by page and creating a final table with all the votes for that congress. I used the regular expression (`re`) package in python to capture patterns of text to identify committee names, dates, and senator-vote combinations.
- Example from 1st Congress, page 1:
  
Unedited, straight from `process_scans.py`
```
cmte on foreign officers. Feb 12, 1791 Ha cla, Picenen He ae
Bassett 3; Butler 1; Carroll 4; Dickinson 6jW Ellsworth Elmer
1; Few 1; Foster 1; Gunn 5; Henry 5; Johnston 1; Izard i; King 1;
Langdon 1; Maclay 10; Monroe 1; Read 2; Schuyler 5; Stanton 1;
Strong 2; Wingate 6.
```
Edited
```
cmte on foreign officers. Feb 12, 1791 Ha cla, Picenen He ae
Bassett 3; Butler 1; Carroll 4; Dickinson 6; Ellsworth 2; Elmer
1; Few 1; Foster 1; Gunn 5; Henry 5; Johnston 1; Izard 1; King 1;
Langdon 1; Maclay 10; Monroe 1; Read 2; Schuyler 5; Stanton 1;
Strong 2; Wingate 6.
```
  - **Committees** - anything from the start of a new line to a `.` or `,`, but not including something that starts with a word, then a number (e.g. `Strong 2; Wingate 6.`), to avoid including name and vote combinations
    - Here we have `cmte on foreign officers`
  - **Dates** - any patterns which contain a month or first 3 letters of a month, then a one or 2 digit number then `,`, then 4 digit number (`Mon(th) DD, YYYY`)
    - Here we have `Feb 12, 1791`
  - **Senator and Vote** - the pattern, name + 1 or 2 digit number followed by punctuation. This should be `;` for ease of use, but the program can pick up other forms of punctuation or characters - `)}>?,:;.` in case there is a character recognition mistake. This pattern excludeds months and dates. Parsing for names and votes starts is only for the range starting at the beginning of the line below each committee to the line of the next committee.
    - This pattern collects all name and vote combinations in a list 
