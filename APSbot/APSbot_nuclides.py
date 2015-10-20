import pywikibot
import csv
from pywikibot.data import api

# Property values from live wikidata:
p_stated_in = 'P248'
p_half_life = 'P2114'
p_ref_url = 'P854'
p_retrieved = 'P813'
p_title = 'P1476'
nndc_qid = 'Q16821319'

retrieval_date = pywikibot.WbTime(year=2015, month=10, day=15)

precision = 10 ** -10

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()


def get_item(id):
    item = pywikibot.ItemPage(repo, id)
    item.get()
    return item


def check_claim_and_uncert(item, property, data):
    """
    Requires a property, value, uncertainty and unit and returns boolean.
    Returns the claim that fits into the defined precision or None.
    """
    item_dict = item.get()
    value, uncert, unit = data
    value, uncert = float(value), float(uncert)
    try:
        claims = item_dict['claims'][property]
    except:
        return None

    try:
        claim_exists = False
        uncert_set = False
        for claim in claims:
            wb_quant = claim.getTarget()
            delta_amount = wb_quant.amount - value
            if abs(delta_amount) < precision:
                claim_exists = True
            delta_lower = wb_quant.amount - wb_quant.lowerBound
            delta_upper = wb_quant.upperBound - wb_quant.amount
            check_lower = abs(uncert - delta_lower) < precision
            check_upper = abs(delta_upper - uncert) < precision
            if check_upper and check_lower:
                uncert_set = True
# Also need to check unit?

            if claim_exists and uncert_set:
                return claim
    except:
        return None


def check_source_set(claim, source_map):
    source_claims = claim.getSources()
    if len(source_claims) == 0:
        return False

    for source in source_claims:
        all_properties_present = True
        for property in source_map.keys():
            target_type, source_value = source_map[property]
            try:
                sources_with_property = source[property]
            except:
                continue
            found = False
            if target_type == 'item':
                found = source_value in map(lambda src: src.target.id, sources_with_property)
            elif target_type == 'string':
                found = source_value in map(lambda src: src.target, sources_with_property)
            if not found:
                all_properties_present = False
                break
        if all_properties_present:
            return True
    return False


def add_quantity_claim(item, property, data):
    value, uncert, unit = data
    value, uncert = float(value), float(uncert)
    claim = pywikibot.Claim(repo, property)
    unit_url = 'http://www.wikidata.org/entity/{0}'.format(unit)
    wb_quant = pywikibot.WbQuantity(value, unit = unit_url, error = uncert)
    claim.setTarget(wb_quant)
    item.addClaim(claim, bot=True, summary="Adding half-life claim from NNDC.")
    return claim


def create_source_claim(claim, source_map):
    source_claims = []
    for property in source_map.keys():
        target_type, source_value = source_map[property]
        source_claim = pywikibot.Claim(repo, property, isReference=True)
        if (target_type == 'item'):
            source_page = pywikibot.ItemPage(repo, source_value)
            source_claim.setTarget(source_page)
        else:
            source_claim.setTarget(source_value)
        source_claims.append(source_claim)
    claim.addSources(source_claims, bot=True)
    return True

def process_nndc_data(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            nuclide_qid, half_life, uncertainty, time_unit, time_unit_string, nuclide_name, nndc_url = row
            nuclide = get_item(nuclide_qid)
            hl_claim = check_claim_and_uncert(nuclide, p_half_life, [half_life, uncertainty, time_unit])
            if (hl_claim is None):
                print('New entry: {0}+-{1}{2} for {3} ({4})'.format(
                    half_life, uncertainty, time_unit_string, nuclide_qid,
                    nuclide_name))
                new_claim = add_quantity_claim(nuclide, p_half_life, [half_life, uncertainty, time_unit])
                source_map = {p_stated_in: ['item', nndc_qid],
# monolingual text not supported by pywikibot yet?
#                          p_title: ['monolingualtext', {'text': 'Half life data from NuDat 2.6 database', 'language': 'en'}],
                          p_ref_url: ['string', nndc_url],
                          p_retrieved: ['date', retrieval_date]}
                print('Add source: {0}'.format(nndc_url))
                create_source_claim(new_claim, source_map)
            else:
                source_map = {p_stated_in: ['item', nndc_qid],
#                          p_title: ['monolingualtext', {'text': 'Half life data from NuDat 2.6 database', 'language': 'en'}],
                          p_ref_url: ['string', nndc_url]}
                if not check_source_set(hl_claim, source_map):
                    source_map[p_retrieved] = ['date', retrieval_date]
                    create_source_claim(hl_claim, source_map)

process_nndc_data('test.csv')
