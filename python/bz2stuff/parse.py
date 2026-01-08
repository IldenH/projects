import re

birth_dates = [
"| birth_date = {{birth-date and age|16 November 1960}}",
"| birth_date        = {{bya|1958}}",
"| birth_date = {{Birth date and age|1973|3|24|df=y}}",
"| birth_date  = {{birth date|1927|12|17|df=yes}}",
"|birth_date= {{Birth-date|February 20, 1840}}",
"| birth_date          = {{Birth date|1889|04|20|df=y}}",
"| birth_date   = {{birth date and age|1965|12|24|df=y}} ",
]

death_dates = [
"| death_date        = &lt;!-- {{death date and age|YYYY|MM|DD|YYYY|MM|DD}} (death date 1st) --&gt;",
"| death_date =",
"| death_date = {{death date and age|2020|1|2|1927|12|17|df=yes}}",
"|death_date= {{Death date and age|14 Sept 1911|20 February 1840}}",
"| death_date          = {{Death date and age|1945|04|30|1889|04|20|df=y}}",
"| death_date = ",
"| death_date ="
]

other_dates = [
    "{{Short description|Chinese Liu Song dynasty prince (429–453)}}",
    """'''Liu Wu''' ({{zh|t=劉戊|s=刘戊|p=Liú Wù}}, died 154 BC) was the son of [[Liu Yingke]], Prince Yi of [[Chu Kingdom (Han dynasty)|Chu]], and grandson of [[Liu Jiao (prince)|Liu Jiao]], Prince Yuan of Chu. After the short reign of his father, he inherited the title Prince of Chu in 174 BC.<ref name=Han14>{{cite book|url=http://zh.wikisource.org/wiki/漢書/卷014|language=Chinese|title=Book of Han|last=Ban Biao|authorlink=Ban Biao|last2=Ban Gu|authorlink2=Ban Gu|last3=Ban Zhao|authorlink3=Ban Zhao|chapter=諸侯王表|trans-chapter=Table of nobles related to the imperial clan|volume=14|accessdate=16 June 2011}}</ref> In 155 BC, [[Empress Dowager Bo]], grandmother of [[Emperor Jing of Han|Emperor Jing]], died. Liu Wu was caught drinking during the grieving period, so Emperor Jing reduced the size of his fiefdom. Wu was later convinced to join the [[Rebellion of the Seven States]] by [[Liu Pi (prince)|Liu Pi]] despite objections from his prime minister and tutor. Liu Wu put both of them to death.""",
]

YEAR_REGEX = re.compile(
    r"\b([0-9]{1,4})\b"
)

DAYS_MONTH = 31

def parse_year(s: str) -> list[int]:
    return [
        year
        for m in YEAR_REGEX.findall(s) or []
        if (year := int(m)) > DAYS_MONTH
    ]
