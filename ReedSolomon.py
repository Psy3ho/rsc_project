class ReedSolomon:
    # Finite fields
    # obsahuje konecny pocet prvkov
    # je to mnozina na ktorej su definovane operacie nasobenia scitania odcitania a delenia
    # primitivny prvok pola je nenulovy
    # ---
    # anti-logarithms
    # 2^9
    # vytvorenie listu s 512 elementami
    gf_exp = [0] * 512

    # logarithms
    # 2^8
    # vytvorenie listu s 256 elementami
    gf_log = [0] * 256



    # Inicializacny konstruktor pre GF
    def __init__(self):
        # pre kazdu moznu hodnotu v galoisovom poli vykoname vypocet logaritmu a antilogaritmu
        self.gf_exp[0] = 1
        byteValu = 1
        for bytePos in range(1, 255):

            #generator==2 or a power of 2
            byteValu <<= 1 # multiply by 2 (change 1 by another number y to multiply by a power of 2^y)
            if (byteValu & 0x100): # similar to x >= 256, but a lot faster (because 0x100 == 256)
                byteValu ^= 0x11d # substract the primary polynomial to the current value

            # aktualizujeme elementy v poliach
            self.gf_exp[bytePos] = byteValu # vypocitame anti-log a ulozime ho do tabulky
            self.gf_log[byteValu] = bytePos # vypocitame log zaroven

        # zdvojnasobime velkost tabulky lebo ju pouzijeme hlavne na nasobenie dvoch cisiel GF
        for bytePos in range(255, 512):
            self.gf_exp[bytePos] = self.gf_exp[bytePos - 255]



    ## Galois primitivne operacie
    # -----

    #Galois addition - scitavanie
    # x - prva hodnota, y - druha hodnota
    def __gfAdd(self, x, y):
        return (x,y)

    #Galois addition - delenie
    # x - prva hodnota, y - druha hodnota
    def __gfSub(self, x, y):
        return (x,y)


    # Galois multiplication - nasobenie
    # x - nasobenec, y - nasobitel

    def __gfMult(self, x, y):

        # skontrolujeme parametre
        if ((x == 0) or (y == 0)):
            vysledok = 0
        else:
            # vykoname nasobenie
            vysledok = self.gf_log[x] + self.gf_log[y]
            vysledok = self.gf_exp[vysledok]

        # vratime vysledok
        return (vysledok)



    # Galois division - delenie
    # x - delenec, y - delitel

    def __gfDivi(self, x, y):

        # skontrolujeme delitel
        if (y == 0):
            raise ZeroDivisionError() # chybove hlasenie - neda sa delit nulou

        # skontrolujeme delenec
        if (x == 0):
            vysledok = 0
        else:
            # vykoname delenie
            vysledok = self.gf_log[x] - self.gf_log[y]
            vysledok += 255
            vysledok = self.gf_exp[vysledok]

        # vratime vysledok
        return (vysledok)


    ## GALOIS polynomialne operacie
    # ----- potrebujeme ich pre RSC

    # Polynomial addition - polynomialne scitavanie v GF
    # x - prva hodnota, y - druha hodnota
    def _gfPolyAdd(self, x, y):
        # inicializujeme sucet polynomu
        vysledok = [0] * max(len(x), len(y))

        # spracujeme prvy doplnok
        for i in range(0, len(x)):
            vysledok[i + len(vysledok) - len(x)] = x[i]

        # spracujeme druhy doplnok
        for i in range(0, len(y)):
            vysledok[i + len(vysledok) - len(y)] ^= y[i]

        # vratime vysledok
        return (vysledok)


    # Polynomial multiplication - polynomialne nasobenie v GF
    # x - prva hodnota, y - druha hodnota
    def _gfPolyMult(self, x, y):
        # inicializacia pre pole vysledku
        vysledok = len(x) + len(y) - 1
        vysledok = [0] * vysledok

        # vynasobime polynomi(vynasobime kazdy koeficient x vsetkymi koeficientami y)
        for i in range(0, len(y)):
            for j in range(0, len(x)):
                vysledok[j + i] ^= self.__gfMult(x[j], y[i])

        # vrati vysledok
        return (vysledok)


    # Polynomial scaling - vynasobenie polynomov skalarom
    # x - polynomialna hodnota
    # y - hodnota scale
    def _gfPolyScale(self, x, y):
        # incializujeme scale polynom
        vysledok = [0] * len(x)

        # zacneme scaling
        for i in range(0, len(x)):
            vysledok[i] = self.__gfMult(x[i], y)

        # vrati vysledok
        return (vysledok)


    # Polynomial evaluation - polynomialne zhodnocovanie
    # x: hodnota polynomu
    # y: nezavysla hodnota
    # z: zavisla hodnota
    def _gfPolyEval(self, x, y):
        # inicializujeme vysledok polynomu
        z = x[0]

        # zhodnotime polynom
        for i in range(1, len(x)):
            temporary = self.__gfMult(z, y)
            temporary = temporary ^ x[i]
            z = temporary

        # vratime vysledok
        return (z)



    ## REED-SOLOMON
    # -----

    # RS generator polynomial - generator polynomov
    # reed solomon vyuziva generator polynomov
    # tato funkcia vypocita generator polynomu pre dany pocet symbolov korekcie chyb
    # errSize - pocet chybnych symbolov
    def _rsGenPoly(self, errSize):
        vysledok = [1]

        for i in range(0, errSize):
            temporary = [1, self.gf_exp[i]]
            vysledok = self._gfPolyMult(vysledok, temporary)

        # vrati vysledok
        return (vysledok)



    ## REED-SOLOMON ENCODING - kodovanie
    # ------
    # message - vstupna sprava
    # errSize - pocet chybnych symbolov
    # outBuffer - vystupny buffer / vystupna sprava
    def RSEncode(self, message, errSize):

        # pripravime generator polynomov
        polyGen = self._rsGenPoly(errSize)

        # pripravime vystupny buffer
        # outBuffer = (len(message) + errSize)
        outBuffer = (len(message) + len(polyGen)-1)
        outBuffer = [0] * outBuffer



        # inicializujeme vystupny buffer
        # outBuffer[:len(message)] = message
        for i in range(0, len(message)):
            mesgChar = message[i]
            outBuffer[i] = ord(mesgChar)

        # zacneme kodovanie
        for i in range(0, len(message)):
            mesgChar = outBuffer[i]
            if (mesgChar != 0):
                for j in range(0, len(polyGen)):
                    temporary = self.__gfMult(polyGen[j], mesgChar)
                    outBuffer[i + j] ^= temporary


        # dokoncime vystupny buffer
        # outBuffer[:len(message)] = message
        for i in range(0, len(message)):
            mesgChar = message[i]
            outBuffer[i] = ord(mesgChar)

        # vratime vystupny buffer
        return (outBuffer)


    ## REED-SOLOMON DECODING - dekodovanie
    # -----


    # vygenerujeme syndrom polynomu
    # message - sprava
    # errSize - pocet chybnych
    def _rsSyndPoly(self, message, errSize):
        # inicializume vysledny polynom
        vysledok = [0] * errSize

        # vypocitame polynomicke vyrazy
        for i in range(0, errSize):
            temporary = self.gf_exp[i]
            vysledok[i] = self._gfPolyEval(message, temporary)

        # vrati vysledok
        return (vysledok)



    # The Forney algorithm
    # syndrome - syndrom polynomu
    # erase - zoznam vymazanych
    # errSize - pocet chybnych
    # polynom - lokator chybneho polynomu
    def _rsForney(self, syndrome, erase, errSize):
        # vytvorime kopiu syndromu polynomu
        polynom = list(syndrome)

        # vypocitame polynomicke vyrazy
        for i in range(0, len(erase)):
            temporaryX = errSize - 1 - erase[i]
            temporaryX = self.gf_exp[temporaryX]
            for j in range(0, len(polynom) - 1):
                temporaryY = self.__gfMult(polynom[j], temporaryX)
                temporaryY ^= polynom[j + 1]
                polynom[j] = temporaryY
            polynom.pop()

        # vrati chybny polynom
        return (polynom)

    # Lokacia chyby spravy
    # location - lokacia chybneho polynomu
    # errSize - pocet chybnych
    def _rsFindErr(self, location, errSize):
        # inicializacia lokalnych premennych
        # errPoly - chybny polynom
        # temp - lokalna premenna polynomu
        errPoly = [1]
        tempPoly = [1]

        # vygenerujeme lokator chybnych polynomov
        # - Berklekamp-Massey algorithm
        for i in range(0, len(location)): # i - pozicia syndrom polynomu
            tempPoly.append(0)
            termSynd = location[i]

            for j in range(1, len(errPoly)): # j - pozicia chyby
                termPoly = errPoly[len(errPoly) - j - 1]
                termPoly = self.__gfMult(termPoly, location[i - j])
                termSynd ^= termPoly

            if (termSynd != 0):
                if (len(tempPoly) > len(errPoly)):
                    tNewP = self._gfPolyScale(tempPoly, termSynd)
                    tempPoly = self._gfPolyScale(errPoly, self.__gfDivi(1, termSynd))
                    errPoly = tNewP

                tempValu = self._gfPolyScale(tempPoly, termSynd)
                errPoly = self._gfPolyAdd(errPoly, tempValu)

        # spocitanie poctu chyb
        errCount = len(errPoly) - 1
        if ((errCount * 2) > len(location)):
            print("Prilis vela chyb pre opravu spravy")
            return (None)
        else:
            print("\r\r")
            print("Pocet najdenych chyb: ", errCount," chyby s ", len(location), " opravovacimi znakmi")

        # Vypocitanie polynomialnych nul
        errList = []
        for errPos in range(0, errSize):
            errZed = self._gfPolyEval(errPoly, self.gf_exp[255 - errPos])
            if (errZed == 0):
                errZed = errSize - errPos - 1
                errList.append(errZed)

        if (len(errList) != errCount):
            print ("Nepodarilo sa lokalizovat chyby")
            return (None)
        else:
            return (errList)

    # Oprava chyb
    # message - sprava
    # syndrome - syndrom polynomu
    # errList - list chyb
    def _rsCorrect(self, message, syndrome, errList):
        # pripravime lokalizacny polynom
        polyLoci = [1]
        for i in range(0, len(errList)): # i - pozicia chyby
            errTerm = len(message) - errList[i] - 1
            errTerm = self.gf_exp[errTerm]
            polyLoci = self._gfPolyMult(polyLoci, [errTerm, 1])

        # pripravime polynom vyhodnocovania chyb
        errEval = syndrome[0:len(errList)]
        errEval.reverse()
        errEval = self._gfPolyMult(errEval, polyLoci)

        tMark = len(errEval) - len(errList)
        errEval = errEval[tMark:len(errEval)]

        # polynom lokatora chyb minus parne vyrazy
        errLoci = polyLoci[len(polyLoci) % 1 : len(polyLoci) : 2]

        # zacneme opravovat
        for i in range(0, len(errList)):
            errByte = errList[i] - len(message) + 256
            errByte = self.gf_exp[errByte]

            errValu = self._gfPolyEval(errEval, errByte)

            errAdj = self.__gfMult(errByte, errByte)
            errAdj = self._gfPolyEval(errLoci, errAdj)

            mesgByte = self.__gfMult(errByte, errAdj)
            mesgByte = self.__gfDivi(errValu, mesgByte)
            message[errList[i]] ^= mesgByte

            #vratime opravenu spravu
        return (message)

    # Main decode routine - hlavna dekodovacia rutina vsetko dokopy pre dekodovanie
    # message - sprava
    # errSize - pocet chybnych symbolov
    def RSDecode(self, message, errSize):

        # inicializujeme vyrovnavaciu pamat kodu
        codeBuffer = list(message)

        # spocitame pocet poskodenych
        eraseCount = []
        for i in range(0, len(codeBuffer)): # i - pozicia danej casti spravy
            if (codeBuffer[i] < 0):
                codeBuffer[i] = 0
                eraseCount.append(i)
        if (len(eraseCount) > errSize):
            print ("Prilis vela poskodenych")
            return (None)

        # pripravime syndrom polynomu
        polySynd = self._rsSyndPoly(codeBuffer, errSize)
        if (max(polySynd) == 0):
            print ("Sprava nema chyby")
            return (codeBuffer)

        # pripravime lokator chybnych polynomov
        errLoci = self._rsForney(polySynd, eraseCount, len(codeBuffer))

        # lokalizuje chyby v sprave
        errList = self._rsFindErr(errLoci, len(codeBuffer))
        if (errList == None):
            print ("Nepodarilo sa najst ziadne chyby")
            return (None)
        else:
            print ("Najdene chyby na poziciach: ", errList, " (pocitame od nuly)")

        # zacneme s opravou chybnych pozicii
        outMesg = self._rsCorrect(codeBuffer, polySynd, (eraseCount + errList))
        return (outMesg)



# Testovaci script = main Test
reedSolomonTest = ReedSolomon()

# nastavime parametre spravy
sprava = "Stastne a vesele vianoce pan Ing. Michal Kuba, PhD."
pocetChyb = 3 #pocet vlozenych chyb
opravovaciKod = 6 #error correcting code - cim viac ty lepsie

print("posleme spravu: ", sprava)
print ("\r\r")

# zakodujeme spravu
zakodovanaSprava = reedSolomonTest.RSEncode(sprava, opravovaciKod)
zakodovanaSpravaPreKontrolu = reedSolomonTest.RSEncode(sprava, opravovaciKod)
print ("Zakodovana sprava:")
print(zakodovanaSprava)
print ("\r\r")

# vytvorime chyby na danych poziciach
zakodovanaSprava[3] = 89
zakodovanaSprava[7] = 8
zakodovanaSprava[10] = 1
# zakodovanaSprava[16] = 2
# zakodovanaSprava[20] = 3
# zakodovanaSprava[21] = 3
# zakodovanaSprava[22] = 3
# zakodovanaSprava[23] = 3
# zakodovanaSprava[14] = 3
# zakodovanaSprava[1] = 3
# zakodovanaSprava[2] = 3
#zakodovanaSprava[5] = 3
#zakodovanaSprava[4] = 3
print ("Zakodovana sprava( s ", pocetChyb,"  chybou/ami):")
print(zakodovanaSprava)
print(([chr(x) for x in zakodovanaSprava]))

# dekodujeme spravu a skusime opravit chyby
sprava = reedSolomonTest.RSDecode(zakodovanaSprava, opravovaciKod)
print ("\r\r")
print ("Dekodovana sprava:")
print(sprava)

if (sprava == zakodovanaSpravaPreKontrolu):
    print ("\r\r")
    print ("Spravu sa podarilo uspesne zakodovat dekodovat a opravit jej chyby")
    print ("\r\r")
    print(([chr(x) for x in sprava]))
else:
    print("Spravu sa nepodarilo uspesne opravit")



