from trytond.pool import Pool
from . import citas_controller
from . import specialtySpanish
def register():
    Pool.register(
        module='sicalis_citas', type_='model')
