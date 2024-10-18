import json
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import re
from queue import LifoQueue


class Tree:
    def __init__(self, dic, *args, **kwargs):
        # Default case
        self.json = json.dumps(dic, indent=4)
        self.content = str(dic.get("content", ""))
        try:
            self.children = {
                x["value"]: Tree(x["tree"]) for x in dic.get("options", [])
            }
        except KeyError:
            raise KeyError("Each of the options must have a value and a tree key.")

        self.height = max([x.height for x in self.children.values()], default=0) + 1
        if self.children:
            self.width = sum([x.width for x in self.children.values()])
        else:
            self.width = 1

    def to_json(self, path):
        with open(path, "w") as f:
            f.write(self.json)

    @classmethod
    def from_json(cls, path: str):
        with open(path) as f:
            resp = cls(json.load(f))

        return resp

    @staticmethod
    def parse_python(code, permeated=None):
        if permeated is None:
            permeated = []
        indent = re.search(r"^(\s*)", code[0]).group(1)
        subtrees = []
        initial_clause = None
        cur_clause = None
        cur_subtree = []
        start = False

        for line in code:
            if not start and not re.search(f"^{indent}if\\b", line):
                permeated.append(line)
            elif clause := re.search(f"^{indent}if\\s(.+):", line):
                cur_clause = clause.group(1)
                if initial_clause is None:
                    initial_clause = cur_clause
                start = True
            elif start and re.search(f"^{indent}\\s+", line):
                cur_subtree.append(line)
            elif start and re.search(f"^{indent}elif\\s+(.+):", line):
                subtrees.append((cur_clause, cur_subtree[:]))
                cur_clause = re.search(f"^{indent}elif\\s+(.+):", line).group(1)
                cur_subtree = []
            elif start and re.search(f"^{indent}else", line):
                subtrees.append((cur_clause, cur_subtree[:]))
                cur_clause = "else"
                cur_subtree = []
        else:
            subtrees.append((cur_clause, cur_subtree[:]))

        subtrees = [
            {"value": x[0], "tree": Tree.parse_python(x[1], permeated[:])}
            for x in subtrees
            if x[1]
        ]

        if initial_clause is not None:
            return {"content": initial_clause.strip(), "options": subtrees}
        else:
            return {"content": "\n".join([x.strip() for x in permeated])}

    @classmethod
    def from_python(cls, path: str):
        """
        This code transforms a python if-elif-else-match block to the json notation used in this class.
        """
        with open(path, "r") as f:
            code = f.readlines()

        return cls(Tree.parse_python(code))

    def compute_total_width(self, node_width, gap_width):
        return self.width * node_width + (self.width - 1) * gap_width

    def compute_total_height(self, node_height, gap_height):
        return self.height * node_height + (self.height - 1) * gap_height

    def plot(
        self,
        node_width=30,
        node_height=20,
        gap_width=10,
        gap_height=30,
        x_init=0,
        y_init=0,
        fig=None,
        ax=None,
        node_color="#0377fc",
        text_color="white",
        arrow_label_color="black",
        arrow_color="red",
    ):
        total_width = self.compute_total_width(node_width, gap_width)
        total_height = self.compute_total_height(node_height, gap_height)

        if not fig and not ax:
            fig, ax = plt.subplots(1, 1)
            ax.set_xlim([-10, total_width])
            ax.set_ylim([-total_height, 10])
            ax.axis("off")

        ax.add_patch(
            Ellipse(
                (total_width / 2.0 + x_init, -node_height / 2.0 + y_init),
                node_width,
                node_height,
                fill=True,
                color=node_color,
            )
        )
        ax.text(
            total_width / 2.0 + x_init,
            -node_height / 2.0 + y_init,
            self.content,
            horizontalalignment="center",
            verticalalignment="center",
            color=text_color,
            fontsize=8,
            fontweight="bold",
        )

        x_exit = x_init
        for name, child in self.children.items():
            x_label = (
                total_width / 2.0
                + x_init
                + x_exit
                + child.compute_total_width(node_width, gap_width) / 2.0
            ) / 2.0
            y_label = -node_height - gap_height / 2.0 + y_init
            if x_label > total_width / 2.0 + x_init:
                ax.text(
                    x_label + 2,
                    y_label,
                    name,
                    horizontalalignment="left",
                    verticalalignment="bottom",
                    color=arrow_label_color,
                    fontsize=6,
                )
            else:
                ax.text(
                    x_label - 2,
                    y_label,
                    name,
                    horizontalalignment="right",
                    verticalalignment="bottom",
                    color=arrow_label_color,
                    fontsize=6,
                )
            ax.arrow(
                total_width / 2.0 + x_init,
                -node_height + y_init,
                x_exit
                + child.compute_total_width(node_width, gap_width) / 2.0
                - (total_width / 2.0 + x_init),
                -gap_height,
                length_includes_head=True,
                head_width=1,
                color=arrow_color,
            )

            child.plot(
                node_width,
                node_height,
                gap_width,
                gap_height,
                x_exit,
                y_init - node_height - gap_height,
                fig,
                ax,
                node_color,
                text_color,
                arrow_label_color,
                arrow_color,
            )
            x_exit += child.compute_total_width(node_width, gap_width) + gap_width

        return fig, ax


if __name__ == "__main__":
    path = "/home/saul/tree_drawing/ejemplo.py"
    tree = Tree.from_python(path)
    fig, ax = tree.plot(node_width=60)
    fig.savefig("resultado.png")
    with open("resultado.json", "w") as f:
        f.write(tree.json)
