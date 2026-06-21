# USDA Query Defaults

Use these defaults when the user does not specify brand, restaurant, or preparation.

| User phrase | Item | USDA query | Notes |
| --- | --- | --- | --- |
| huevos, eggs | eggs | egg whole cooked hard-boiled | Plain cooked default. Ask if fried, scrambled with oil/butter, or cheese matters. |
| claras | egg whites | egg white cooked | Use only when user says whites/claras. |
| frijoles, beans | beans | black beans cooked | Generic frijoles default. Ask/type-adjust for bayo, pinto, refried, charro. |
| frijoles refritos | refried beans | refried beans | Preparation matters; prefer explicit refried query. |
| cafe, café, coffee | coffee | coffee brewed | Black brewed coffee default. Split milk/sugar separately if mentioned. |
| leche | milk | milk whole | Ask low-fat/skim/plant milk if relevant. |
| arroz | rice | rice white cooked | Ask brown/white only if needed. |
| pollo | chicken | chicken breast cooked roasted | Ask cut/preparation if fried, sauced, or skin-on. |
| tortilla maiz | corn tortilla | tortilla corn | Prefer unit grams if possible. |

## Selection Rules

- Prefer generic USDA foods over branded foods unless user names a brand.
- Prefer cooked entries when user describes prepared food.
- Prefer plain preparations over fried/oily preparations unless stated.
- Record the selected API match in `api_food_name`.
- Put mapping assumptions in `notes`.
