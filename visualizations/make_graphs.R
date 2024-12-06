
party_votes <- read.csv("C:/Users/elswl/Documents/MomSenateData/EarlyAmericanSenateData/useful_tables/VotesByParty.csv")

head(party_votes)
ggplot(party_votes, aes(x = congress, y = TotalVotes, color = party, group = party)) +
       geom_line(linewidth = 1) + 
       geom_point(size = 2) + 
       labs(title = "Votes Over Time by Party",
           x = "Congress",
             y = "Votes",
             color = "Party") +
       theme_minimal() 

