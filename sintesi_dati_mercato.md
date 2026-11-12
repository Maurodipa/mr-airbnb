# SINTESI DEI DATI RACCOLTI (DATA LAKE AIRBNB)

* **Orizzonte temporale rilevato:** `2026-09-20` ➔ `2027-01-31` (99 date)
* **Appartamenti monitorati nel cluster:** 51
* **Totale slot monitorati (giorni x alloggi):** 5,023

## 1. Analisi Mensile: Occupazione e Tariffe Medie Nette
| Mese | Date Rilevate | Alloggi Monitorati | Tasso Occupazione | Prezzo Min | 25° Perc | Tariffa Calendario Mediana Competitor | 75° Perc | Prezzo Max | Tuo Prezzo Calendario Consigliato |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2026-09** | 1 gg | 25 | **88.0%** | 153 € | 170 € | **186 €** | 206 € | 225 € | **244 €** |
| **2026-10** | 6 gg | 306 | **81.4%** | 89 € | 165 € | **195 €** | 241 € | 494 € | **254 €** |
| **2026-11** | 30 gg | 1530 | **43.9%** | 72 € | 119 € | **140 €** | 175 € | 284 € | **187 €** |
| **2026-12** | 31 gg | 1581 | **32.7%** | 76 € | 127 € | **146 €** | 203 € | 811 € | **194 €** |
| **2027-01** | 31 gg | 1581 | **22.5%** | 66 € | 117 € | **142 €** | 191 € | 811 € | **189 €** |

## 2. Dettaglio Giorni Speciali e Picchi di Domanda
| Data Speciale | Festività / Evento | Occupazione | Guadagno Netto (Mediana) | Tariffa Calendario | Alloggi Rimasti Liberi |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `2026-10-31` | Halloween | **72.5%** | 205 € | **267 €** | 14 su 51 |
| `2026-12-24` | Vigilia Natale | **39.2%** | 185 € | **242 €** | 31 su 51 |
| `2026-12-25` | Natale | **41.2%** | 182 € | **239 €** | 30 su 51 |
| `2026-12-31` | Capodanno | **45.1%** | 206 € | **267 €** | 28 su 51 |
| `2027-01-01` | Capodanno (1 gen) | **49.0%** | 199 € | **259 €** | 26 su 51 |
| `2027-01-06` | Epifania | **25.5%** | 156 € | **206 €** | 38 su 51 |

## 3. Confronto Struttura dei Costi: Tuo Appartamento vs Mercato
Questa tabella confronta la tua configurazione fissa delle pulizie con la media dei competitor nel tuo cluster (51 appartamenti).
| Metrica | Il Tuo Appartamento | Mediana Competitor |
| :--- | :---: | :---: |
| **Costi Pulizia (Tariffa mostrata a Calendario)** | 59.00 € | 59.00 € |
| **Costi Pulizia (Rimborso Netto in tasca)** | **50.00 €** | **50.00 €** |