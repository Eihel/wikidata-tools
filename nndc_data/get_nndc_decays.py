# -*- coding: utf-8 -*-
#
import nuclides
import nndc_data
import codecs
import math
import sys

#

UNKNOWN_QID = 'Q4294967294'

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

nuclide_provider_class = nuclides.WdqNuclideProvider

nuclide_provider = nuclide_provider_class('en')

nuclides = nuclide_provider.get_nuclides()

nuclides_by_protons_neutrons = {}
for nuclide in nuclides:
    nuclides_by_protons_neutrons['{}_{}'.format(nuclide.atomic_number, nuclide.neutron_number)] = nuclide.item_id

# Should filter out where nuclides data already includes this value...

for nuclide in nuclides:
    z = nuclide.atomic_number
    n = nuclide.neutron_number
    decay_modes, source_url = nndc_data.nndc_decay_modes(z, n)
    for decay_mode in decay_modes:
        mode = decay_mode['mode']
        mode_qid = nndc_data.nndc_decay_id(mode)
        pct = None
        if 'pct' in decay_mode:
            pct = decay_mode['pct']
        pn = nndc_data.protons_neutrons_after_decay(z, n, mode_qid)
        if pn is not None:
            key = '{}_{}'.format(pn[0], pn[1])
            if key in nuclides_by_protons_neutrons:
                decays_to = nuclides_by_protons_neutrons[key]
            else:
                decays_to = UNKNOWN_QID
        else:
            decays_to = UNKNOWN_QID
        print u"{0},{1},{2},{3},{4},{5},{6}".format(nuclide.item_id,
            mode, mode_qid, pct, decays_to, nuclide.label, source_url)
