i <- 1

packs <- c('DT',
           'dplyr',
           'stringr',
           'ggplot2',
           'tidyr',
           'purrr',
           'knitr',
           'scales',
           'ggrepel',
           'wordcloud',
           'naniar',
           'gdata',
           'lubridate',
           'collapsibleTree',
           'jsonlite',
           'data.table',
           'readr')

for(x in packs){
  print(i)
  print(x)
  #pacman::p_load(x)
  i <- i+1
}
