# Data source

`hsn_bcd.json` maps 8-digit HSN tariff items to their **Basic Customs Duty** rate, parsed from
India's **Customs Tariff Act, First Schedule** (the official import tariff, a public document).

- 11,972 usable entries (11,772 ad-valorem `NN%` rates + 203 `Free`).
- ~126 rows use specific duties (e.g. `Rs 42 per kg`) and are skipped, the duty engine here
  computes ad-valorem percentages only. This is reported, not hidden.

Spot-checks against the schedule: cashew in shell (`08013100`) = 30%, desiccated coconut
(`08011100`) = 70%, motor car (`87032391`) = 125%, personal computer (`84713010`) = 0%.

## Regenerate

`hsn_bcd.json` is derived, not authored. To rebuild it, extract the First Schedule PDF to text
and run the parser:

```bash
pdftotext -layout customs_tariff_first_schedule.pdf tariff.txt
python parse_tariff.py tariff.txt          # writes data/hsn_bcd.json
```

The IGST rate is **not** in this file, IGST is levied under the GST law, not the customs tariff
so it is supplied as an input at duty time.
