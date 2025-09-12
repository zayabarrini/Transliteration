# Composing of Ebook with subtitles + Return Subtitles translation and Transliteration in various languages

Input: zip of .srt
Output: zip of zip with combinations in various languages
Translations: -en, -de-ch, -ru-de-ch, etc
generate [1,n]-language combinations if we have many languages

# Issues
Translation takes a long time
for 36 subtitles, it took almost 10h to translate and transliterate chinese = Almost 17 minutes for subtitle
To combine using Web Tools, takes about 1-2 minutes by subtitle: translate and merge

# Menu
Improvements: 
format_tvseries_folders - combine_into_ebook: receive folder, rename files, clean files, see if it's series or movies, create md, create ebook 


clean subtitles folder: path-to-folder
Series: name_SxEx
    single: format_tvseries.py
    bulk: format_tvseries_folders.py

Movies: 
    single: combine_files.py
    bulk: combine_files_folder.py

## add_metadata.py


## clean_subtitles.sh


## combine_add_metadata.py


## combine_files.py


## combine_files_folder.py


## format_filenames.py


## format_filenames.sh -> /usr/local/bin/format_filenames.sh


## format_tvseries.py


## format_tvseries_folders.py


## zip2zip.py


## zip2zipMultilingual.py


