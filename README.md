# EarlyAmericanSenateData
This repository contains data related to early American Senate activities, focused on votes on committee participants from the  1<sup>st</sup> to 16<sup>th</sup> Congresses. The data come from voting rolls in the National Archives and the [*Biographical Directory of the United States Congress*](https://bioguide.congress.gov/). This project has been devoted to digitizing and partially cleaning notes made by Dr. Terri Halperin from these primary sources for use in research and analysis.

## 📜 Data Overview
- **Source**: The main data originates from historical records of the United States Senate. These records document committee votes, attendance, and dates from the 1<sup>st</sup> to 16<sup>th</sup> Congresses. Biographical data (including state, age, party, etc.) come from the [*Biographical Directory of the United States Congress*](https://bioguide.congress.gov/)
  
- **Content**: Votes for committee participation
    - Name of committee
    - Date of vote on committee membership
    - Names of senators and number votes they received
- **Format**:
    - Text files and scanned images containing raw and extracted data
    - Cleaned and tabulated data (in progress) for structured analysis
    - Vote data merged with biographical data (in progress)

## 🔍 Current Goals and Plans
1. **Data Cleaning**: 
   - Correct errors in names, dates, and formatting from the raw text
   - Standardize names and entries to align with historical accuracy (e.g., correcting "Ellswort" to "Ellsworth")
     
2. **Data Structuring**:
   - Create a structured database containing tables with information on:
     - Senators by Congress
     - Votes by Senator by Committee
     - Committee by Congress

3. **Analysis and Visualization**:
   - Explore trends in voting behavior, committee composition, and legislative activity
   - Create visualizations to illustrate findings

4. **Documentation**:
   - Develop thorough documentation of the dataset to support reproducibility and future research

## 🛠 How to Use This Repository

1. **View the Data**:
   - Raw text files and scanned images are available in the `scans_and_text` folder
   - Vote data can be found in the `vote_data` folder
   - Merged data with biographical info can be found in the `Merged_Data` folder

2. **Contribute**:
   - If you notice errors or have suggestions for improvement, feel free to submit a pull request or open an issue
