import csv,json,re,time,random,requests
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import urlsplit

DATE='2026-08-06'
EPS=['https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://overpass.nchc.org.tw/api/interpreter','https://overpass.osm.ch/api/interpreter']
DATA='''nyc|New York City / North Jersey|NY|40.7128|-74.006|90
la|Los Angeles / Orange County|CA|34.0522|-118.2437|100
chi|Chicago|IL|41.8781|-87.6298|95
dfw|Dallas-Fort Worth|TX|32.7767|-96.797|110
hou|Houston|TX|29.7604|-95.3698|110
dc|DC / Baltimore / Northern Virginia|VA|38.9072|-77.0369|110
phi|Philadelphia / South Jersey|PA|39.9526|-75.1652|95
mia|South Florida|FL|25.7617|-80.1918|120
atl|Atlanta|GA|33.749|-84.388|110
phx|Phoenix|AZ|33.4484|-112.074|100
sea|Seattle / Tacoma|WA|47.6062|-122.3321|110
bos|Boston / Providence|MA|42.3601|-71.0589|105
sfb|San Francisco Bay|CA|37.7749|-122.4194|115
den|Denver / Front Range|CO|39.7392|-104.9903|120
det|Detroit / Ann Arbor|MI|42.3314|-83.0458|110
msp|Minneapolis-Saint Paul|MN|44.9778|-93.265|105
sd|San Diego|CA|32.7157|-117.1611|85
tpa|Tampa Bay|FL|27.9506|-82.4572|105
orl|Orlando / Central Florida|FL|28.5383|-81.3792|110
clt|Charlotte / Upstate SC|NC|35.2271|-80.8431|115
ral|Raleigh-Durham / Greensboro|NC|35.7796|-78.6382|110
bna|Nashville|TN|36.1627|-86.7816|105
pdx|Portland / Salem|OR|45.5152|-122.6784|110
sac|Sacramento / Stockton|CA|38.5816|-121.4944|105
las|Las Vegas|NV|36.1699|-115.1398|90
aus|Austin / San Antonio|TX|30.2672|-97.7431|130
cle|Cleveland / Akron|OH|41.4993|-81.6944|105
cmh|Columbus / Dayton|OH|39.9612|-82.9988|110
cvg|Cincinnati / Northern KY|OH|39.1031|-84.512|95
ind|Indianapolis|IN|39.7684|-86.1581|105
stl|St. Louis|MO|38.627|-90.1994|100
kc|Kansas City|MO|39.0997|-94.5786|115
slc|Salt Lake / Provo / Ogden|UT|40.7608|-111.891|110
nol|New Orleans / Baton Rouge|LA|29.9511|-90.0715|120
ric|Richmond / Fredericksburg|VA|37.5407|-77.436|120
orf|Hampton Roads|VA|36.8529|-75.978|95
bhm|Birmingham / Montgomery|AL|33.5186|-86.8104|130
okc|Oklahoma City|OK|35.4676|-97.5164|110
tul|Tulsa / NW Arkansas|OK|36.154|-95.9928|115
abq|Albuquerque / Santa Fe|NM|35.0844|-106.6504|115
oma|Omaha / Lincoln|NE|41.2565|-95.9345|110
dsm|Des Moines / Ames|IA|41.5868|-93.625|105
boi|Boise|ID|43.615|-116.2023|105
jax|Jacksonville|FL|30.3322|-81.6557|110
mem|Memphis|TN|35.1495|-90.049|105
lou|Louisville / Lexington|KY|38.2527|-85.7585|120
mke|Milwaukee / Madison|WI|43.0389|-87.9065|120
pit|Pittsburgh / Morgantown|PA|40.4406|-79.9959|110
buf|Buffalo / Rochester / Syracuse|NY|42.8864|-78.8784|125
hfd|Connecticut / Springfield|CT|41.7658|-72.6734|105
me|Southern Maine|ME|43.6591|-70.2568|125
nh|New Hampshire|NH|42.9956|-71.4548|100
vt|Vermont|VT|44.4759|-73.2121|140
ri|Rhode Island|RI|41.824|-71.4128|70
de|Delaware / Eastern Shore|DE|39.1582|-75.5244|95
sc|Columbia / Charleston / Myrtle Beach|SC|33.8361|-80.8987|165
sav|Savannah / Hilton Head|GA|32.0809|-81.0912|105
ms|Jackson / Gulf Coast|MS|32.2988|-90.1848|165
ar|Little Rock / Hot Springs|AR|34.7465|-92.2896|130
nd|North Dakota metros|ND|46.8772|-96.7898|180
sdak|South Dakota metros|SD|43.5446|-96.7311|170
mt|Montana metros|MT|46.8797|-110.3626|320
wy|Wyoming metros|WY|42.8666|-106.3131|290
reno|Reno / Tahoe|NV|39.5296|-119.8138|120
spk|Spokane / Coeur d'Alene|WA|47.6588|-117.426|115
eug|Eugene / Central Oregon|OR|44.0521|-123.0868|180
elp|El Paso / Las Cruces|TX|31.7619|-106.485|110
stx|South Texas|TX|27.8006|-97.3964|190
wtx|West Texas|TX|33.5779|-101.8552|280
hnl|Oahu|HI|21.3069|-157.8583|75
hib|Hawaii Island / Maui|HI|19.8968|-155.5828|175
anc|Anchorage / Mat-Su|AK|61.2181|-149.9003|150
fai|Fairbanks|AK|64.8378|-147.7164|100
wv|West Virginia metros|WV|38.3498|-81.6326|155
md|Annapolis / Eastern Shore|MD|38.9784|-76.4922|105
nj|Central / South New Jersey|NJ|40.0583|-74.4057|105'''
REG=[(a,b,c,float(d),float(e),int(float(f)*1000)) for a,b,c,d,e,f in (x.split('|') for x in DATA.splitlines())]
NAME=r'Realty|Real Estate|Realtor|Brokerage|Properties|Property Management|Home Buyers|House Buyers|Cash Buyers|We Buy Houses|Investments|Investment Group|Acquisitions|Land Buyers|Capital Partners|Residential Real Estate|Commercial Real Estate|Real Estate Development|RE/MAX|Keller Williams|Coldwell Banker|Century 21|Sotheby|Compass Real Estate|eXp Realty|Berkshire Hathaway|Douglas Elliman|ERA Real Estate'
KEYS=['phone','contact:phone','mobile','contact:mobile','email','contact:email','website','contact:website']
COLS=['record_type','source_batch','region_id','region_name','confidence_rank','lead_id','confidence_score','confidence_grade','company_name','contact_name','contact_title','broad_group','category','headquarters_state','target_states','target_markets','property_types','strategy','price_min_usd','price_max_usd','units_min','units_max','beds_min','sqft_min','condition','other_criteria','financing','closing_speed','accepts_assignments','email','phone','contact_status','website','address','city','postal_code','latitude','longitude','source_url','source_domain','source_type','source_data_timestamp','criteria_source_type','contact_source_type','buy_box_detail_level','public_data_gaps','confidence_notes','verification_status','last_verified','official_pages_reviewed','website_fetch_status','osm_element_type','osm_element_id','research_method','data_license']
def cl(v):return re.sub(r'\s+',' ',str(v or '')).strip()
def norm_url(v):
 v=cl(v)
 if not v:return ''
 if not re.match(r'https?://',v,re.I):v='https://'+v
 try:return v if urlsplit(v).netloc else ''
 except:return ''
def dom(v):
 try:return urlsplit(v).netloc.lower().removeprefix('www.')
 except:return ''
def email(v):
 for x in re.split(r'[;,\s]+',cl(v).replace('mailto:','').split('?')[0]):
  x=x.lower()
  if re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}",x,re.I) and not re.search(r'example\.|sentry\.io|wixpress\.com|\.(png|jpg|gif|svg|css|js)$',x):return x
 return ''
def phone(v):
 for x in re.split(r'[;,/]|\bor\b',cl(v),flags=re.I):
  d=re.sub(r'\D','',x)
  if len(d)==11 and d[0]=='1':d=d[1:]
  if len(d)==10:return f'({d[:3]}) {d[3:6]}-{d[6:]}'
 return cl(v)[:80] if v else ''
def query(r):
 _,_,_,lat,lon,rad=r;c=[f'nwr["office"~"^(estate_agent|property_management|real_estate_agent|real_estate|estate_management)$"](around:{rad},{lat},{lon});',f'nwr["shop"="estate_agent"](around:{rad},{lat},{lon});']
 for k in KEYS:c += [f'nwr["name"~"{NAME}",i]["{k}"](around:{rad},{lat},{lon});',f'nwr["brand"~"{NAME}",i]["{k}"](around:{rad},{lat},{lon});']
 return '[out:json][timeout:180];('+''.join(c)+');out center tags 1800;'
def fetch(i,r):
 eps=EPS[i%len(EPS):]+EPS[:i%len(EPS)];last=''
 for a in range(7):
  try:
   z=requests.post(eps[a%len(eps)],data={'data':query(r)},headers={'User-Agent':'PublicRealEstateContactResearch/5.0'},timeout=230);z.raise_for_status();return r,z.json().get('elements',[]),''
  except Exception as e:last=str(e);time.sleep(min(20,2+a*2+random.random()*2))
 return r,[],last
def relevant(n,t):
 s=n.lower();p=re.search(r'realty|real estate|realtor|broker|properties|property management|home buyers?|house buyers?|cash buyers?|we buy houses|invest|acquisition|land buyer|capital partners|commercial real estate|development|re/max|keller williams|coldwell banker|century 21|sotheby|compass|exp realty|berkshire hathaway',s) or t.get('office') in ['estate_agent','property_management','real_estate_agent','real_estate','estate_management'] or t.get('shop')=='estate_agent'
 return bool(p) and not (re.search(r'mortgage|title company|insurance|attorney|law firm|apprais|home inspect|moving|storage|photograph|architect|cleaning|roofing|plumbing|furniture|hardware|credit union|\bbank\b',s) and not re.search(r'realty|real estate|realtor|properties|property management|home buyer|invest',s))
def category(n,t):
 s=(n+' '+cl(t.get('description'))).lower()
 if re.search(r'we buy houses|cash home buyer|cash buyer|home buyers?|house buyers?',s):return 'Direct Residential Cash Buyer','Cash Home Buyer / Local Investor','Direct cash purchase'
 if re.search(r'investment|acquisition|capital partners|holdings|\bfund\b',s):return 'Investor / Investment Company','Real Estate Investor / Acquisitions Company','Public investor/acquisition signal'
 if re.search(r'property management|rental management',s):return 'Property Management / Rental Operator','Property Management Company','Property management'
 if re.search(r'commercial real estate|investment sales',s):return 'Realtor / Brokerage','Commercial Real Estate Brokerage','Commercial brokerage/investment sales'
 if re.search(r'development|home builder',s):return 'Builder / Developer','Real Estate Developer / Builder','Development'
 return 'Realtor / Brokerage','Real Estate Brokerage / Agent','Residential brokerage'
def make(r,e):
 rid,rn,st,*_=r;t=e.get('tags',{});n=cl(t.get('name') or t.get('brand') or t.get('operator'))
 if not n or not relevant(n,t):return None
 p=phone(t.get('contact:phone') or t.get('phone') or t.get('contact:mobile') or t.get('mobile'));m=email(t.get('contact:email') or t.get('email'));w=norm_url(t.get('contact:website') or t.get('website') or t.get('url'))
 if not(p or m or w):return None
 ce=e.get('center',{});city=cl(t.get('addr:city') or t.get('addr:town') or t.get('addr:village'));state=cl(t.get('addr:state') or st);line=' '.join(filter(None,[cl(t.get('addr:housenumber')),cl(t.get('addr:street'))]));address=cl(t.get('addr:full') or ', '.join(filter(None,[line,city,state,cl(t.get('addr:postcode'))])));g,c,strat=category(n,t);score=30+15*bool(m)+15*bool(p)+5*bool(m and p)+8*bool(w)+4*bool(address or city)+5*bool('Investor' in g or 'Cash Buyer' in g);score=min(100,score);grade='A' if score>=90 else 'B' if score>=75 else 'C' if score>=55 else 'D';status='Direct email + phone' if m and p else 'Email only' if m else 'Phone only' if p else 'Website only';gaps=[]
 for val,label in [(m,'public email'),(p,'public phone'),(w,'website')]:
  if not val:gaps.append(label)
 gaps += ['explicit property criteria','price range','closing speed']
 return {'record_type':'CONTACT','source_batch':'OSM-GHA-20260806','region_id':rid,'region_name':rn,'confidence_rank':'','lead_id':'','confidence_score':score,'confidence_grade':grade,'company_name':n,'contact_name':'','contact_title':'','broad_group':g,'category':c,'headquarters_state':state,'target_states':state,'target_markets':', '.join(filter(None,[city,state])),'property_types':'','strategy':strat,'price_min_usd':'','price_max_usd':'','units_min':'','units_max':'','beds_min':'','sqft_min':'','condition':'','other_criteria':cl(t.get('description') or t.get('note')),'financing':'Cash' if 'Cash Buyer' in g else '','closing_speed':'','accepts_assignments':'','email':m,'phone':p,'contact_status':status,'website':w,'address':address,'city':city,'postal_code':cl(t.get('addr:postcode')),'latitude':str(e.get('lat',ce.get('lat',''))),'longitude':str(e.get('lon',ce.get('lon',''))),'source_url':f"https://www.openstreetmap.org/{e.get('type')}/{e.get('id')}",'source_domain':'; '.join(filter(None,['openstreetmap.org',dom(w)])),'source_type':'OpenStreetMap public business record','source_data_timestamp':cl(e.get('timestamp')),'criteria_source_type':'Public business-name/category signal only; exact buy box not confirmed','contact_source_type':'; '.join(filter(None,['Public OSM email' if m else '','Public OSM phone' if p else '','Public OSM website' if w else ''])),'buy_box_detail_level':'Basic','public_data_gaps':'; '.join(gaps),'confidence_notes':'Public real-estate business record with available contact fields; exact active-buyer status and buy box not directly confirmed.','verification_status':'Public-source researched; not directly contacted','last_verified':DATE,'official_pages_reviewed':'','website_fetch_status':'not_reviewed','osm_element_type':cl(e.get('type')),'osm_element_id':cl(e.get('id')),'research_method':'OpenStreetMap public business/contact discovery','data_license':'OpenStreetMap data © OpenStreetMap contributors, ODbL 1.0'}
def main():
 rows=[];errs=[]
 with ThreadPoolExecutor(max_workers=7) as ex:
  fs={ex.submit(fetch,i,r):r for i,r in enumerate(REG)}
  for j,f in enumerate(as_completed(fs),1):
   r,els,err=f.result();z=[x for x in (make(r,e) for e in els) if x];rows+=z
   if err:errs.append({'region':r[0],'error':err})
   print(j,len(REG),r[0],len(els),len(z),bool(err),flush=True)
 best={}
 for x in rows:
  n=re.sub(r'[^a-z0-9]+',' ',x['company_name'].lower()).strip();em=x['email'].lower();ph=re.sub(r'\D','',x['phone'])[-10:];wd=dom(x['website']);k='e:'+em if em else 'p:'+ph+'|'+n[:35] if ph else 'w:'+wd+'|'+n[:35] if wd else 'o:'+x['osm_element_type']+':'+x['osm_element_id']
  if k not in best or int(x['confidence_score'])>int(best[k]['confidence_score']):best[k]=x
 rows=list(best.values());rows.sort(key=lambda x:(-int(x['confidence_score']),x['company_name'].lower()))
 for i,x in enumerate(rows,1):x['confidence_rank']=i;x['lead_id']=f'OSM-GHA-{i:05d}'
 with open('osm_real_estate_contacts.csv','w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(rows)
 s={'records':len(rows),'with_email':sum(bool(x['email']) for x in rows),'with_phone':sum(bool(x['phone']) for x in rows),'with_both':sum(bool(x['email'] and x['phone']) for x in rows),'grades':{g:sum(x['confidence_grade']==g for x in rows) for g in 'ABCD'},'region_errors':errs};open('crawl_summary.json','w').write(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
if __name__=='__main__':main()
