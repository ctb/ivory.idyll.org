import sys
print ''

for i in sys.argv[1:]:
    print open(i).read()
    print ''
