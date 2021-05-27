#! /usr/bin/python3

from urllib.request import Request, urlopen

req = Request('https://www.melhorcambio.com/dolar-hoje', headers={'User-Agent': 'Mozilla/5.0'})
content = urlopen(req).read()
content = str(content)
find = '<input type="hidden" value="'
position = int(content.index(find) + len(find))
dolar = content[position : position + 4]

req = Request('https://www.melhorcambio.com/euro-hoje', headers={'User-Agent': 'Mozilla/5.0'})
content = urlopen(req).read()
content = str(content)
find = '<input type="hidden" value="'
position = int(content.index(find) + len(find))
euro = content[position : position + 4]

req = Request('https://www.climatempo.com.br/previsao-do-tempo/cidade/469/jacarei-sp', headers={'User-Agent': 'Mozilla/5.0'})
content = urlopen(req).read()
content = str(content)
find = 'max-temp-1">'
position = int(content.index(find) + len(find))
maxima = content[position : position + 2]

req = Request('https://www.climatempo.com.br/previsao-do-tempo/cidade/469/jacarei-sp', headers={'User-Agent': 'Mozilla/5.0'})
content = urlopen(req).read()
content = str(content)
find = 'min-temp-1">'
position = int(content.index(find) + len(find))
minima = content[position : position + 1]

print(f"Dollar Hoje: U$ {dolar}")
print(f"Euro Hoje: U$ {euro}")
print()
print("==== TEMPERATURA EM JACAREÍ ====")
print(f"Máx: {maxima}°")
print(f"Min {minima}°")