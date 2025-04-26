from ninja import Router
from ninja_extra import NinjaExtraAPI, api_controller, ControllerBase, route
from ninja.constants import NOT_SET
from django.http import JsonResponse


api = NinjaExtraAPI()

router = Router()


@router.get('status')
def health_check(request):
    return JsonResponse({'message': 'OK'})


@api_controller('cart', auth=NOT_SET, permissions=[])
class CartController(ControllerBase):
    @route.post('/init_cart')
    def init_cart(self):
        return {
            "data": True
        }


controllers = [
    CartController,
]
