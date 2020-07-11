library(dplyr)

# Rscript generate_html directory_with_data_folder
#    saves html files to updates/

args <- commandArgs(trailingOnly = TRUE)

dir <- getwd() 
if (length(args == 1)) {
    dir <- args[1]
}

file <- paste0(dir,"/data/state_and_county.RData")
    
load(file)

formatChange <- function(x, hospitalizations = FALSE) {
  
  n <- length(x)
  
  if (hospitalizations) {
    current <- x[n]
    prior <- x[n-7]
  } else {
    current <- sum(x[(n-6):n])
    prior <- sum(x[ (n-13):(n-7)])
  }
  
  pc <- (current - prior)
  dir <- ""
  if (pc > 0) {
    dir <- '(an increase of ' 
  } else if (pc < 0)  {
    dir <- '(a decrease of '
  }
  
  if (pc == 0) {
    return(list(current = current, change = "(no change from last week)"))
  }
  
  if (current < 10 || prior < 10) {
      dir <- '(similar to last week)' 
      return(list(current = current, change = dir))
  } 
  x <- round(abs(pc/  prior * 100),1)
  list(current = current, change = paste0(dir, x, '%)'))
}

generate_html_update <- function(x, county = NULL, saveFile = FALSE) {

  n <- nrow(x)

  cases <- formatChange(x$new_cases)
  deaths <- formatChange(x$new_deaths)
  
  hh <- NULL
  if ('hospitalizations' %in% colnames(x)) {
    hh <- x$hospitalizations
  } else {
    hh <- x$hospitalization
  }
  hosps <- formatChange(hh)
  
  
  d2 <- as.Date(x$date[n])


  msg1 <- paste('<li>there were', cases$current, 'new daily reported confirmed/probable cases', cases$change, "</li>\n")
  msg2 <- paste('<li>there were', deaths$current, 'new daily reported COVID-19 associated deaths', deaths$change, "</li>\n")
  msg3 <- paste('<li>there were', hosps$current, 'current hospitalizations', hosps$change, "</li>\n")
  
  state <- "In the <b>state of CT</b>"
  c2 <- ""
  if (!is.null(county)) {
    state <- paste0("In <b>", county, "</b> county")
    c2 <- "County"
  }
  
  msg<- paste(msg1, msg2, msg3)
  msg <- paste0('<p>', state, ', for the week ending on ', format(d2, "%m/%d/%Y"), ',\n<ul>\n', 
              paste0(msg, collapse = ', '), "</ul>")

  
  msg1 <- paste0("<h3>EIDA/COVID in CT Weekly ", c2, " Update ", format(as.Date(Sys.time()), "(%m/%d/%Y)</h3>"))
  msg1 <- paste0(msg1, "\n\n",msg)

  
  url <- "https://eida.easternct.edu/shiny/app/covid-ct"
  url_text <- 'COVID-19/CT home page'
  
  fileName <- 'CT'
  if (!is.null(county)) {
    fileName <- gsub(' ', '_', county)
    url <- paste0(url, "/?_inputs_&maintab=\"County Data\"&county=\"",county, "\"")
    url <- gsub(' ', "%20", url)
    url <- gsub('"', "%22", url)
  
    url_text <- gsub("home ", "", url_text)
    url_text <- paste(url_text, 'for', county, 'county')
  }
  
  msg1 <- paste0(msg1,"\n\n<p>For up-to-date information, click <a href = ", url, ">here</a>",
                 " to access the ", url_text, ".</p>")
       
  if (saveFile) {
    write(msg1, file = paste0('updates/',fileName, "_update_", Sys.Date(), ".html"))
  } else {
    return(msg1)
  }
}

generate_html_update(df_state, saveFile = TRUE)

counties <- unique(df_county$county)

for (mycounty in counties) {
  generate_html_update(df_county %>% filter(county == mycounty), county = mycounty, saveFile = TRUE)
}

generate_html_update(df_county %>% filter(county == mycounty), county = mycounty, saveFile = FALSE)

