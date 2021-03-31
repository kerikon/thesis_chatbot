import osmium as osm


class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.osm_data = []

    def tag_inventory(self, elem, elem_type):
        for tag in elem.tags:
            self.osm_data.append([elem_type,
                                   elem.id,
                                   len(elem.tags),
                                   tag.k,
                                   tag.v])

    def relation(self, r):
        rel_types = ['corridor', 'area', 'junction', 'room', 'elevator', 'level', 'building']
        rel_type = r.tags['type']
        if rel_type in rel_types:
            if 'junction_type' in r.tags:
                self.osm_data.append({'id': r.id, 'ref': r.tags['ref'], 'type': rel_type,
                                      'junction_type': r.tags['junction_type']})
            elif rel_type == 'level':
                self.osm_data.append({'id': r.id, 'ref': r.tags['ref'], 'type': rel_type,
                                      'name': r.tags['name']})
            else:
                self.osm_data.append({'id': r.id, 'ref': r.tags['ref'], 'type': rel_type})
