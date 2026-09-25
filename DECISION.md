# DECISION — beslutningsarkiv

> Dette er et **arkiv af beslutninger**, ikke en plan. Den operative state ligger
> i `IMPLEMENTATION_PLAN.md`. Hver beslutning er skrevet med den viden og de
> forbehold den blev truffet under.

## Betaling: Stripe (24. september 2026)

Lemon Squeezy afviste kontoen, og Gumroad blev droppet. Alt salg kører nu gennem
Stripe-kontoen Mahope.dk. Kontrakten med betalingslinks, product keys og
licens-API står i `docs/stripe-kontrakt.md`.

Konsekvens: ingen side, klient eller CI-job har Stripe-nøgler. Sider linker til
betalingslinks, og klienter taler med licens-API'et. Lemon Squeezy genoplives
aldrig.

## Open-core (24. september 2026)

Gratis værktøjer er gode og open source, ikke demoer. Den betalte udgave er
markant bedre til teams og bureauer: batch, flere maskiner, rapporter,
integrationer og prioriteret support. Betalt indhold og betalt kode ligger i
private repos, aldrig i de offentlige.

## Sourcing: kernen er platformuafhængig (23. august 2026)

Et værktøj der kun virker i WordPress skærer størstedelen af markedet væk og
binder os til wp.org's regler. Kernen tager en almindelig URL og virker på alt;
WordPress-plugin, web og CLI er indpakninger omkring den samme kerne.

## Drift uden Mads (23. august 2026)

Intet i produkterne må kræve, at han svarer på noget, godkender noget eller
leverer noget. Testen: rejser han væk i tre måneder, tjener det stadig penge?
Derfor ingen kundesupport, ingen manuel levering og ingen beslutninger han skal
tage for at driften fortsætter.

## Budget: 35 kr brugt af 1.000 kr

Se `BUDGET.md`. Loftet er godkendt af Mads 23. august 2026 og overskrides aldrig
uden hans ja.
