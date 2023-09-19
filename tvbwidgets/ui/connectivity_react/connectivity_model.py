from traitlets import HasTraits, Bool, List, Integer, Unicode, Float


class ConnectivityDTO(HasTraits):
    region_labels = List()
    weights = List()
    undirected = Bool()
    tract_lengths = List()
    speed = List()
    centres = List()
    cortical = List(trait=Bool(), allow_none=True)
    hemispheres = List(trait=Bool(), allow_none=True)
    orientations = List(allow_none=True)
    areas = List(trait=Float(), allow_none=True)
    idelays = List(trait=Integer(), allow_none=True)
    delays = List(trait=Float(), allow_none=True)
    number_of_regions = Integer()
    number_of_connections = Integer()
    parent_connectivity = Unicode(allow_none=True)
    saved_selection = List(trait=Integer())
