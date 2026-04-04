# Reasoning

This repo is one of my newest projects. I'm learning about how to build distributed systems and how to build APIs, and I'm working it in junction
to my hiperfixation: AI.

This README will give all instructions of how to use this API, wich is currently under developement.

## The Background
This API system is designed to consume the Ollama API locally (on server side), using 2 agents for the process of creating an knownledge graph,
using prompt engineering. It is not "reasoning" on the full meaning, but an automated search system that get a problem and gives it a solution.
I've already designed some systems like this for my College course [here's the repo](https://github.com/pedrovinicius123/api-ollama-reasoning.git).
It worked partially, for I'm designing this new system, with more organization and intrerpretability.

### Working
Basically I have 2 AIs interacting with each other: the "Creative" one and the "Critical" one. The Creative AI will propose new nodes, generate new connections
and grow the graph, while the Critic will evalue it and refit for more accuracy and confiability. One of the issues is that this can become an theater,
with both sides alucinating. The solution is to design an genetic algorithm wich filters the most accurate "ideas" and passes it to the next generation.
There is an score assigned to each edge of the graph, whose can be unidiretional (implication: $\Rightarrow$) or bidiretional (equality: $\Leftrightarrow$), and it will lead the search for a solution of the
original problem.

A problem or question can be described as two contradicting propositions: one must be true, while other false; if we find an inconsistency on
the first affirmative, the second affirmative will be true, and virse-versa. As well as, if an affirmative is proven true, the other is false.
Of course, consistency is not everything, as the Gödel Incompleteness states, but if there is an cicle where all nodes are true, and the last one on the starting node
then this node is also true. Mathematically speaking:

$$x \rightarrow y \wedge y \rightarrow z$$
$$z \rightarrow x$$

By transitive rule, we can affirm that $x \leftrightarrow z$ (though $x \rightarrow z$ and $z \rightarrow x$)
wich means that if z is true, x is also.

The system will use this thought to eliminate inconsistent cicles and reinforce the accuracy of the system. It will also use an global optimizer
(the genetic algorithm I spoke before), and construct graphs for this schedule, crossing then over for better nodes.

## Routes
For this project, the designed routes and specific request methods are:
. /nodes/graph [PATCH, GET] => PATCH for adding edges, GET for retrieve all
. /nodes [POST, GET] => POST to add a node and GET to retrieve all
. /nodes/<int:id> [GET] => To retrieve a specific node
