from argparse import ArgumentParser
from os import listdir, mkdir
from os.path import splitext, exists, isdir
from re import sub, findall, finditer, match
from string import capwords

global op
op = False
global opquote
opquote = False

p = ArgumentParser()
p.add_argument("-r", "--recompile", help = "Recompile all of the files", action="store_true")
p.add_argument("--books", help = "List of files to compile", type=str, default="")
args = p.parse_args()

def main(file):
    def replace_html(line):
        line = sub("'", "’", line)
        line = sub("``", "“", line)
        line = sub("\"", "”", line)
        line = sub("--", "–", line)
        return line
    
    def reset_result(title):
        return ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>" + title + "</title><link rel='icon' href='https://rfoxinter.github.io/favicon.ico'/><meta name='viewport' content='width=device-width, initial-scale=1'><meta name='theme-color' content='#157878'><link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap'><link rel='stylesheet' type='text/css' href='https://rfoxinter.github.io/normalize.css'><link rel='stylesheet' type='text/css' href='https://rfoxinter.github.io/style.css'><link rel='stylesheet' type='text/css' href='../plays.css'></head><body>"]
    
    def add_footer(result):
        result.append("<footer class='site-footer'>")
        result.append("<div class='foot'>%PREV%%NEXT%</div>")
        result.append("</footer>")

    def generate_toc(files):
        res = ""
        for i in range(1, len(files)):
            res += "<p><a href='" + files[i][0] + ".html'>" + files[i][1] + "</a></p>"
        return res

    def parse_file(i, files):
        output = open(ttl + "/" + files[i][0] + ".html", "r", encoding="utf-8")
        result = output.read()
        output.close()
        if i == 0:
            result = sub("%PREV%", "", result)
            result = sub("%NEXT%", "", result)
            result = sub("%TOC%", generate_toc(files), result)
            result = sub("<div class='foot'></div>", "<div class='foot_alt'><p><a href='../" + file + ".pdf' target='_blank'>Download PDF</a></p><p><a href='../'>List of works</a></p></div>", result)
            output = open(ttl + "/" + files[i][0] + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
        else:
            result = sub("%PREV%", "<a href='" + files[i - 1][0] + ".html'>" + files[i - 1][1] + "</a>", result)
            result = sub("%NEXT%", "<a href='" + files[(i + 1) % len(files)][0] + ".html'>" + files[(i + 1) % len(files)][1] + "</a>", result)
            output = open(ttl + "/" + files[i][0] + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()


    def convertchar(line):
        global op
        global opquote
        for character in findall(r"\b[A-Z']+(?:'?, [A-Z]+)*\b", line):
            if len(character) > 1:
                if match(r"\b[I|V|X]+\b", character) is None:
                    line = sub(character, "<sc>" + capwords(character) + "</sc>", line, 1)
                else:
                    _line = line.split(character)[0].split(" ")
                    addbrackets = True
                    for l in _line:
                        if l != "" and match(r"<sc>", l) is None:
                            addbrackets = False
                    if addbrackets:
                        line = sub(character, "<span>" + character + "</span>", line, 1)
                if line.find(">,") != -1:
                    op = True
                line = sub(">, ", ">     <i>", line)
            if op:
                line = sub("\n", "</i>\n", line)
                op = False
        line = sub("  ", "   ", line)
        shift = 0
        for quote in finditer("\"", line):
            if opquote:
                opquote = False
            else:
                line = line[:quote.start() + shift] + "``" + line[quote.end() + shift:]
                shift += 1
                opquote = True
        del shift
        return "<p>" + sub("\n", "</p>\n", replace_html(line))

    def convertline(line, itindent):
        global op
        global opquote
        for character in findall(r"\b[A-Z]+(?:'[A-Z]+)*\b", line):
            if len(character) > 1 and (match(r"\b[I|V|X]+\b", character) is None):
                line = sub(character, "<sc>" + capwords(character) + "</sc>", line)
                line = sub(">,", ">", line)
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
            line = line.replace("[", "<center>[")
            op = True
        if line[-2] == "]" and op:
            line = line.replace("]", "]</center>")
            op = False
        line = sub("\[", "<i>[", line)
        line = sub("\]", "]</i>", line)
        line = sub("\\t", "     ", line)
        _line = line.rsplit("   ", 1)
        if itindent:
            line = "   <i>".join(_line)
            if len(_line) > 1:
                line = sub("\\n", "</i>\\n", line)
        return "<p>" + sub("\n", "</p>\n", replace_html(line))

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
                result.append("<br/>\n")
                result.append("\n")
            elif lst[pos] != "\n":
                result.append(convertline(lst[pos], itindent))
                result.append("\n")
            pos += 1
        return pos

    content = open(file + ".txt", "r", encoding="utf-8").readlines()

    title = replace_html(content[0].replace("\n", ""))
    author = content[1].replace("by", "").replace("\n", "")
    result = reset_result(title)
    result.append("<header class='page-header'><h1><i>" + title + "</i></h1><h2>" + author + "</h2></header><main class='main-content'>")
    result.append("%TOC%")
    result.append("</main>")
    add_footer(result)
    result.append("</body>")
    output = open(ttl + "/index.html", "w", encoding="utf-8")
    output.writelines(result)
    output.close()
    files = [["index", "Table of Contents"]]

    pos = 0
    l = len(content)

    act = 0
    scene = 0
    actcontent = ""

    while pos < l:
        if content[pos] == "======================\n":
            result = reset_result("Dramatis Personae")
            result.append("<header class='page-header'><h1>Dramatis Personae</h1></header><main class='main-content'>")
            result.append("\n")
            pos += 1
            pos = list_characters(content, pos, result, l)
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", "Dramatis Personae").lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", "Dramatis Personae").lower(), "Dramatis Personae"])
        elif content[pos] == "============================\n": # Epilogue
            scene += 1
            scenecontent = capwords(content[pos - 2].replace(",", ""))
            result = reset_result(actcontent + " – " + scenecontent)
            result.append("<header class='page-header'><h1>" + actcontent + "</h1><h2>" + scenecontent + "</h2></header><main class='main-content'>")
            result.append("\n")
            content[pos] = content[pos - 1]
            pos = list_scene(content, pos, result, l, False)
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", actcontent + scenecontent).lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", actcontent + scenecontent).lower(), actcontent + " – " + scenecontent])
        elif (content[pos] == "========\n" or content[pos] == "=========\n") and "EPILOGUE" in content[pos - 1]: # Epilogue
            scene += 1
            scenecontent = capwords(content[pos - 1].replace(",", "").replace(".", ""))
            result = reset_result(actcontent + " – " + scenecontent)
            result.append("<header class='page-header'><h1>" + actcontent + "</h1><h2>" + scenecontent + "</h2></header><main class='main-content'>")
            result.append("\n")
            content[pos] = content[pos - 1]
            pos += 2
            pos = list_scene(content, pos, result, l, False)
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", actcontent + scenecontent).lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", actcontent + scenecontent).lower(), actcontent + " – " + scenecontent])
        elif content[pos] == "=========\n" and "INDUCTION" in content[pos - 1]: # Induction
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            pos += 1
        elif content[pos] == "==========\n" and "INDUCTION" in content[pos - 1]: # Induction
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            result = reset_result(actcontent)
            result.append("<header class='page-header'><h1>" + actcontent + "</h1></header><main class='main-content'>")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, False)
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", actcontent).lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", actcontent).lower(), actcontent])
        elif content[pos] == "============\n" or (content[pos] == "========\n" and "PROLOGUE" in content[pos - 1]) or (content[pos] == "========\n" and "Preface" in content[pos - 1]): # Prologue
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1].replace("THE ", ""))
            result = reset_result(actcontent)
            result.append("<header class='page-header'><h1>" + actcontent + "</h1></header><main class='main-content'>")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, False)
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", actcontent).lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", actcontent).lower(), actcontent])
        elif content[pos] == "=======\n" or content[pos] == "========\n": # Scene
            scene += 1
            scenecontent = capwords(content[pos - 1])
            result = reset_result(actcontent + " – " + scenecontent)
            result.append("<header class='page-header'><h1>" + actcontent + "</h1><h2>" + scenecontent + "</h2></header><main class='main-content'>")
            result.append("\n")
            pos += 1
            pos = list_scene(content, pos, result, l, "chorus" not in content[pos - 2].lower())
            result.append("</main>")
            add_footer(result)
            result.append("</body>")
            output = open(ttl + "/" + sub(" ", "", actcontent + scenecontent).lower() + ".html", "w", encoding="utf-8")
            output.writelines(result)
            output.close()
            files.append([sub(" ", "", actcontent + scenecontent).lower(), actcontent + " – " + scenecontent])
        elif content[pos] == "=====\n": # Act
            act += 1
            scene = 0
            actcontent = capwords(content[pos - 1])
            pos += 1
        pos += 1
    
    for i in range(len(files)):
        parse_file(i, files)

def sortkey(x):
    if x[0] == "A" and "A" <= x[1] <= "Z":
        x = x[1:len(x)]
    return x.replace("The", "").replace("Part", "")

def main_index():
    result = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><title>Shakespeare’s works</title><link rel='icon' href='https://rfoxinter.github.io/favicon.ico'/><meta name='viewport' content='width=device-width, initial-scale=1'><meta name='theme-color' content='#157878'><link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,700;1,400;1,700&display=swap'><link rel='stylesheet' type='text/css' href='https://rfoxinter.github.io/normalize.css'><link rel='stylesheet' type='text/css' href='https://rfoxinter.github.io/style.css'><link rel='stylesheet' type='text/css' href='plays.css'></head><body>"]
    result.append("<header class='page-header'><h1>Shakespeare’s works</h1></header><main class='main-content'>")
    folders = []
    for folder in listdir("."):
        if isdir(folder) and folder[0] != ".":
            folders.append(folder)
    for folder in sorted(folders, key=sortkey):
        title = open(folder + "/index.html", "r", encoding="utf-8").read()
        start = title.find("<h1>")
        end = title.find("</h1>")
        title = title[start + 4:end]
        result.append("<p><a href='" + folder + "'>" + title + "</a></p>")
    result.append("</main>")
    result.append("<footer class='site-footer'>")
    result.append("<div class='foot'></div>")
    result.append("</footer>")
    result.append("</body>")
    output = open("index.html", "w", encoding="utf-8")
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
            if args.recompile or not exists(ttl + "/index.html") or args.books != "":
                print(ttl)
                if not exists("./" + ttl):
                    mkdir("./" + ttl)
                main(ttl)
    main_index()