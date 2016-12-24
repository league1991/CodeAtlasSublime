from grandalf.graphs import Vertex,Edge,Graph
import random
def shuffle(lis):
	result = []
	while lis:
		p = random.randrange(0, len(lis))
		result.append(lis[p])
		lis.pop(p)
	return result

V = [Vertex(data) for data in range(15)]
X = [
(1,5),
(1,9),
(1,7),
(8,13),
(1,6),
(1,0),
(1,3),
(8,14),
(2,11),
(1,4),
(8,12),
(2,10),
(1,8),
(2,1),
]
E = [Edge(V[v],V[w]) for (v,w) in X]
g = Graph(V,E)

print(g.C)
print(g.path(V[1],V[9]))

from grandalf.layouts import SugiyamaLayout
class defaultview(object):
	w,h = 10.0,10.0

sizeList = [
(43.366611790964676,200),
(53.026383008023586,200),
(40.004866773426386,200),
(68.35051437976315,200),
(48.5669151431107,200),
(69.56377621946662,200),
(52.153148511892184,200),
(54.27650767350815,200),
(38.001702916324795,200),
(61.59543225340435,200),
(57.520984909950286,200),
(64.49612302995996,200),
(71.38960484928593,200),
(67.53662520941695,200),
(49.73541984499222,200),
]
for i,v in enumerate(V):
	v.view = defaultview()
	v.view.w, v.view.h = sizeList[i]

packSpace = 4
sug = SugiyamaLayout(g.C[0])
#sug.init_all(roots=[V[0]],inverted_edges=[V[4].e_to(V[0])])
sug.xspace = packSpace
sug.yspace = packSpace
#sug.order_iter = 32
sug.dirvh = 3
sug.init_all()
sug.draw()

# pos:0 (0.0,100.0)
# pos:1 (-62.14111896447103,304.0)
# pos:2 (2.867435005484097,304.0)
# pos:3 (-79.36272225037119,304.0)
# pos:4 (-378.7738580569366,508.0)
# pos:5 (-309.1942538205011,508.0)
# pos:6 (-247.25828385704486,508.0)
# pos:7 (-190.04345576434469,508.0)
# pos:8 (-138.28357561291625,508.0)
# pos:9 (-78.42501252755235,508.0)
# pos:10 (-15.966297766115446,508.0)
# pos:11 (31.318011263602294,508.0)
# pos:12 (-63.59926743717183,712.0)
# pos:13 (-0.9632449099672442,712.0)
# pos:14 (63.59926743717183,712.0)

for i, v in enumerate(g.C[0].sV):
	x,y = (v.view.xy[0],v.view.xy[1])
	print("%s: (%d,%d) bord (%s,%s)"%(v.data,v.view.xy[0],v.view.xy[1], x-sizeList[i][0]/2,x+sizeList[i][0]/2))
# for l in sug.layers:
# 	for n in l:
# 		print(n.view.xy)