# Distance callback
class CreateDistanceCallback(object):
  """Create callback to calculate distances between points."""
  def __init__(self,products):
    self.cha_day = pd.read_csv('changeover_days.csv')
    self.products = products
  def Distance(self, from_product, to_product):
    return self.cha_day[(self.cha_day.From==self.products[from_product]) & 
                        (self.cha_day.To==self.products[to_product])].Days.values[0]

def find_optimal_route(products):
  tsp_size = len(products)
  num_routes = 1
  depot = 0
  if tsp_size > 0:
    routing = pywrapcp.RoutingModel(tsp_size, num_routes, depot)
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    dist_between_nodes = CreateDistanceCallback(products)
    dist_callback = dist_between_nodes.Distance
    routing.SetArcCostEvaluatorOfAllVehicles(dist_callback)
    # Solve, returns a solution if any.
    assignment = routing.SolveWithParameters(search_parameters)
    if assignment:
      print("Total distance: ",assignment.ObjectiveValue())
      # Inspect solution.
      # Only one route here; otherwise iterate from 0 to routing.vehicles() - 1
      route_number = 0
      index = routing.Start(route_number) # Index of the variable for the starting node.
      route = ''
      while not routing.IsEnd(index):
        # Convert variable indices to node indices in the displayed route.
        route += str(products[routing.IndexToNode(index)]) + ' -> '
        index = assignment.Value(routing.NextVar(index))
      route += str(products[routing.IndexToNode(index)])
      print("Route:\n\n" + route)
    else:
      print('No solution found.')
  else:
    print('Specify an instance greater than 0.')

find_optimal_route(['P51', 'P13', 'P33', 'P43', 'P9', 'P8', 'P34', 'P3'])