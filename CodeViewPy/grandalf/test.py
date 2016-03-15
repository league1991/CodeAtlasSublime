from grandalf.graphs import Vertex,Edge,Graph
V = [Vertex(data) for data in range(10)]
X = [(0,1),(0,2),(1,3),(2,3),(4,0),(1,4),(4,5),(5,6),(3,6),(3,7),(6,8),(7,8),(8,9),(5,9)]
E = [Edge(V[v],V[w]) for (v,w) in X]
g = Graph(V,E)

print(g.C)
print(g.path(V[1],V[9]))

from grandalf.layouts import SugiyamaLayout
class defaultview(object):
	w,h = 10,10

for v in V:
	v.view = defaultview()
	
sug = SugiyamaLayout(g.C[0])
#sug.init_all(roots=[V[0]],inverted_edges=[V[4].e_to(V[0])])
sug.init_all()
sug.draw()

for v in g.C[0].sV:
	print("%s: (%d,%d)"%(v.data,v.view.xy[0],v.view.xy[1]))
for l in sug.layers:
	for n in l:
		print(n.view.xy)