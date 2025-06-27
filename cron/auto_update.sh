#!/bin/bash

# Script to fetch all timetables

declare -a groups=("fise_1a_g1"
  "fise_1a_g2"
  "fise_1a_g3"
  "fise_1a_g4"
)

rm -f ./timetables/*.ics

for group in "${groups[@]}"
do
    curl "https://edt.telecomnancy.univ-lorraine.fr/static/${group}.ics" >> "./timetables/${group}.ics"
done
