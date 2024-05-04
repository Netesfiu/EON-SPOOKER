Read in other languages: 
<kbd>[<img title="Magyar" alt="Magyar" src="https://cdn.statically.io/gh/hjnilsson/country-flags/master/svg/hu.svg" width="22">](README.hu.md)</kbd> 
<kbd> [<img title="English" alt="English" src="https://cdn.statically.io/gh/hjnilsson/country-flags/master/svg/us.svg" width="22">](README.en.md)</kbd>

# E.ON W1000 "Spooker"

Ez a repó egy Python szkriptet tartalmaz, amely adatokat az [E.ON W1000 portálról](https://energia.eon-hungaria.hu/W1000/) átalakítani egy nyers YAML fájlba. Ez a YAML fájl aztán másolható a `recorder.import_statistics` szolgáltatásba, ha telepítve van a [frenck/Spook](https://github.com/frenck/spook) integráció. Ajánlom, hogy ezt használd a [hass-w1000-portal](https://github.com/ZsBT/hass-w1000-portal) projektben találhatóval együtt.

## Követelmények

A szkript futtatásához az alábbi függőségek telepítése szükséges:

- Python 3.12.0 (opcionális)
- Hozzáférés az E.ON W1000 portálhoz
- Telepített [Spook](https://github.com/frenck/spook)
    - kérlek, olvasd el az [integráció dokumentációját](https://spook.boo) a telepítéshez

## Adatok beszerzése az E.ON W1000-ről

1. Jelentkezz be a W1000 portálra, [itt](https://energia.eon-hungaria.hu/W1000/Account/Login).
2. Hozz létre egy új munkaterületet, ha még nem hoztál létre egyet sem.
3. A munkaterületen belül hozz létre egy új jelentést a "+" ikonra kattintva, és add hozzá az alábbi görbéket:
    - +A
    - -A
    - DP_1-1:1.8.0*0
    - DP_1-1:2.8.0*0
4. Az "ok" gombra kattintva látnod kell a jelentés adatait.
5. A jelentés oldalán kattints a "day" gombra, majd válaszd ki a "custom" lehetőséget.
6. Írd be a jelentés időintervallumát. A formátum legyen `dd/hh/éééé` (nap/hónap/év).
7. Miután megadtad az időintervallumot, kattints a pipa ikonra.
8. Kattints az "export" linkre a jelentésben, vagy válaszd az exportálás lehetőséget a **≡** menüben.
9. Az export ablakban válaszd ki a `Profile Table` lehetőséget, majd válaszd a `Comma separated values (.csv)` formátumot. Győződj meg róla, hogy a `Include status` opció **nincs bejelölve!**
10. Kattints az exportálásra, majd várj, amíg a fájl letöltődik.

## Szkript használata

1. Klónozd ezt a tárolót a helyi gépedre.
2. Telepítsd a szükséges függőségeket a következő parancs futtatásával:
    ```
    pip install -r requirements.txt
    ```
3. Módosítsd a szkriptet szükség szerint.
4. Indítsd el a szkriptet a következő parancs futtatásával:
    ```
    python EON_SPOOKER.py
    ```
5. A szkript létrehoz egy `import.yaml` és egy `export.yaml` fájlt a szkript helyén.

Alternatív megoldásként használhatja a lefordított végrehajtható fájlt `EON_SPOOKER.exe`, ami [Innen letölthető](https://github.com/Netesfiu/EON_SPOOKER/releases/tag/main). Egyszerűen duplán kattints a futtatható fájlra a szkript futtatásához.

## Adatok importálása a Homeassistantbe

1. Lépj a fejlesztői eszközök>szolgáltatások menüpontra.
2. Keresd meg a `recorder.import_statistics` szolgáltatást.
3. Válaszd ki a mérőóra szenzorodat.
4. Állítsd be a forrást `recorder`-re.
5. Használd a `kWh` mértékegységet.
6. Kapcsold be a `has a sum` opciót.
7. A statisztikák részben illeszd be a megfelelő yaml fájl tartalmát.
8. Kattints a `call_service` gombra.
9. Kész! Most már rendelkezel az összes adattal a megfelelő szenzorban.

### minta yaml konfiguráció:
```yaml
service: recorder.import_statistics
data:
  has_mean: false
  has_sum: true
  statistic_id: sensor.w1000_import
  source: recorder
  unit_of_measurement: kWh
  stats:
    - start: "2021-01-02 00:00:00+02:00"
      sum: 123
    - start: "2021-01-02 01:00:00+02:00"
      sum: 456
    - ...
```

**!!FIGYELEM!!** Nagyon ajánlott biztonsági mentést készíteni, mielőtt bármilyen módosítást végzel a szenzor előzményeinek statisztikáiban, mivel ezek nem visszavonhatók!

## Hozzájárulás

Ha találsz bármilyen problémát, vagy javaslatod van a fejlesztésre, nyugodtan nyiss egy problémát vagy küldj egy pull requestet.

