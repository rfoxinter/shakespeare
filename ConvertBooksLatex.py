from argparse import ArgumentParser
from os import listdir, remove
from os.path import splitext, exists
from re import sub, findall, finditer, match
from string import capwords
from subprocess import run
from subprocess import PIPE

debug = False
global op
op = False
global opquote
opquote = False

p = ArgumentParser()
p.add_argument("-r", "--recompile", help = "Recompile all of the files", action='store_true')
p.add_argument("--books", help = "List of files to compile", type=str, default="")
args = p.parse_args()

def main(file):
    def convertchar(line):
        global op
        global opquote
        for character in findall(r"\b[A-Z']+(?:'?, [A-Z]+)*\b", line):
            if len(character) > 1:
                if match(r"\b[I|V|X]+\b", character) is None:
                    line = sub(character, "\\\\textsc{" + capwords(character) + "}", line, 1)
                else:
                    _line = line.split(character)[0].split(" ")
                    addbrackets = True
                    for l in _line:
                        if l != "" and match(r"\\textsc", l) is None:
                            addbrackets = False
                    if addbrackets:
                        line = sub(character, "{" + character + "}", line, 1)
                if line.find("},") != -1:
                    op = True
                line = sub("}, ", "}\\\\qquad\\\\emph{", line)
            line = sub("  ", "\\\\qquad{}", line)
            if op:
                line = sub("\n", "}\n", line)
                op = False
        shift = 0
        for quote in finditer("\"", line):
            if opquote:
                opquote = False
            else:
                line = line[:quote.start() + shift] + "``" + line[quote.end() + shift:]
                shift += 1
                opquote = True
        del shift
        for exp in findall(r"</.*>", line):
            line = sub(exp, "}", line)
        for exp in findall(r"<.*>", line):
            line = sub(exp, "\\\\emph{", line)
        return line

    def convertline(line, itindent):
        global op
        global opquote
        for character in findall(r"\b[A-Z]+(?:'[A-Z]+)*\b", line):
            if len(character) > 1 and (match(r"\b[I|V|X]+\b", character) is None):
                line = sub(character, "\\\\textsc{" + capwords(character) + "}", line)
                line = sub("},", "}", line)
        shift = 0
        for quote in finditer("\"", line):
            if opquote:
                opquote = False
            else:
                line = line[:quote.start() + shift] + "``" + line[quote.end() + shift:]
                shift += 1
                opquote = True
        del shift
        if line[0] == "[" and (line[-2] == "]" or line.find("]") == -1):
            line = line.replace("[", "{\\centering[")
            op = True
        if line[-2] == "]" and op:
            line = line.replace("]", "]\\par}")
            op = False
        line = sub("\[", "{\\\\itshape[", line)
        line = sub("\]", "]}", line)
        line = sub("\\t", "\\\\qquad{}", line)
        line = sub("   ", "\\\\quad{}", line)
        _line = line.rsplit("\\qquad{}", 1)
        if itindent:
            line = "\\qquad\\textsl{".join(_line)
            if len(_line) > 1:
                line = sub("\\n", "}\\n", line)
        line = sub("  ", " {} ", line)
        return line

    def list_characters(lst, pos, result, l):
        while lst[pos] != '\n' and pos < l:
            result.append(convertchar(lst[pos]))
            result.append("\n")
            pos += 1
        return pos

    def list_scene(lst, pos, result, l, itindent = True):
        prev = lst[pos - 1]
        while pos < l and (pos + 2 >= l or lst[pos + 2][0] != '='):
            if lst[pos] == "\n" and prev != "\n":
                result.append("\\null\n")
                result.append("\n")
            elif lst[pos] != "\n":
                result.append(convertline(lst[pos], itindent))
                result.append("\n")
            pos += 1
        return pos

    content = open(file + ".txt", 'r', encoding="utf-8").readlines()

    title = content[0].replace("\n", "")
    author = content[1].replace('by ', '').replace("\n", "")
    result = ["\\documentclass[a4paper,titlepage,12pt,twoside]{article}\\usepackage[outer=2.5cm, inner=3cm, top=2.5cm, bottom=2.5cm]{geometry}\\usepackage[english]{babel}\\usepackage{hyperref}\\hypersetup{hidelinks,pdftitle={" + title + "},pdfauthor={" + author + "}}\\title{\\emph{\\textbf{" + title + "}}}\\author{" + author + "}\\date{}\\let\\oldsection\\section\\renewcommand{\\section}{\\clearpage\\oldsection}\\usepackage{fancyhdr}\\setlength{\headheight}{15pt}\\makeatletter\\let\\@afterindentfalse\\@afterindenttrue\\@afterindenttrue\\makeatother\\begin{document}\n","\\maketitle\\tableofcontents\\thispagestyle{empty}\\leftskip=1em\\parindent=-1em"]

    pos = 0
    l = len(content)

    act = 0
    scene = 0
    actcontent = ""

    while pos < l:
        if content[pos] == "======================\n":
            result.append("{\leftskip=0em\\section*{Dramatis Personae}}\\label{sec:" + str(act) + "}\\addcontentsline{toc}{section}{Dramatis Personae}\\pagestyle{fancy}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{Dramatis Personae}}")
            result.append("\n")
            pos += 1
            pos = list_characters(content, pos, result, l)
        elif content[pos] == "============================\n": # Epilogue
            scene += 1
            result.append("{\leftskip=0em\\subsection*{" + capwords(content[pos - 1].replace(",", "")) + "}}\\label{subsec:" + str(act) + "." + str(scene) + "}\\addcontentsline{toc}{subsection}{" + capwords(content[pos - 1].replace(",", "")) + "}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{" + actcontent + "}}\\fancyhead[LO,RE]{\\textsc{" + capwords(content[pos - 1].replace(",", "")) + "}}")
            result.append("\n")
            content[pos] = content[pos - 1]
            pos = list_scene(content, pos, result, l, False)
        elif (content[pos] == "========\n" or content[pos] == "=========\n") and "EPILOGUE" in content[pos - 1]: # Epilogue
            scene += 1
            scenecontent = capwords(content[pos - 1].replace(",", "").replace(".", ""))
            result.append("{\leftskip=0em\\subsection*{" + scenecontent + "}}\\label{subsec:" + str(act) + "." + str(scene) + "}\\addcontentsline{toc}{subsection}{" + scenecontent + "}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{" + actcontent + "}}\\fancyhead[LO,RE]{\\textsc{" + scenecontent + "}}")
            result.append("\n")
            content[pos] = content[pos - 1]
            pos += 2
            pos = list_scene(content, pos, result, l, False)
        elif content[pos] == "=========\n" and "INDUCTION" in content[pos - 1]: # Induction
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            result.append("{\leftskip=0em\\section*{" + actcontent + "}}\\label{sec:" + str(act) + "}\\addcontentsline{toc}{section}{" + actcontent + "}")
            result.append("\n")
            pos += 1
        elif content[pos] == "==========\n" and "INDUCTION" in content[pos - 1]: # Induction
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            result.append("{\leftskip=0em\\section*{" + actcontent + "}}\\label{sec:" + str(act) + "}\\addcontentsline{toc}{section}{" + actcontent + "}\\pagestyle{fancy}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{Induction}}")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, False)
        elif content[pos] == "============\n" or (content[pos] == "========\n" and "PROLOGUE" in content[pos - 1]) or (content[pos] == "========\n" and "Preface" in content[pos - 1]): # Prologue
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1].replace("THE ", ""))
            result.append("{\leftskip=0em\\section*{" + actcontent + "}}\\label{sec:" + str(act) + "}\\addcontentsline{toc}{section}{" + actcontent + "}\\pagestyle{fancy}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{Prologue}}")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, False)
        elif content[pos] == "=======\n" or content[pos] == "========\n": # Scene
            scene += 1
            result.append("{\leftskip=0em\\subsection*{" + capwords(content[pos - 1]) + "}}\\label{subsec:" + str(act) + "." + str(scene) + "}\\addcontentsline{toc}{subsection}{" + capwords(content[pos - 1]) + "}\\fancyhead{}\\fancyhead[RO,LE]{\\textsc{" + actcontent + "}}\\fancyhead[LO,RE]{\\textsc{" + capwords(content[pos - 1]) + "}}")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, "chorus" not in content[pos - 2].lower())
        elif content[pos] == "=====\n": # Act
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            result.append("{\leftskip=0em\\section*{" + actcontent + "}}\\label{sec:" + str(act) + "}\\addcontentsline{toc}{section}{" + actcontent + "}")
            result.append("\n")
            pos += 1
        pos += 1

    result.append("\\end{document}")
    output = open(file + ".tex", "w", encoding="utf-8")
    output.writelines(result)
    output.close()

def add_ext(file):
    ttl, _ = splitext(file)
    return ttl + ".txt"

if __name__ == "__main__":
    files = listdir(".") if args.books == "" else map(add_ext ,args.books.split(","))
    for file in files:
        ttl, ext = splitext(file)
        if ext == ".txt":
            if args.recompile or not exists(ttl + ".pdf") or args.books != "":
                print(ttl)
                main(ttl)
                for _ in range(3):
                    run("pdflatex -interaction=nonstopmode -file-line-error " + ttl + ".tex", shell = True, stdout = PIPE, stderr = PIPE, text = True)
                for ext in [".aux", ".log", ".out", ".toc"]:
                    remove(ttl + ext)
                if not debug:
                    remove(ttl + ".tex")