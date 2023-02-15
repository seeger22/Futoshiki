import copy
import numpy as np
import argparse

def listify(lst):
    '''
    turns the states into list of lists
    returnlst = list of lists (2D matrix for the 4x4 puzzle)
    '''
    returnlst = []
    for item in lst:
        nums = [int(x) if x.isnumeric() else x for x in item.split()]
        returnlst.append(nums)
    return returnlst

def printlst(lst, f):
    '''
    formatting the list to print out each item in the list
    '''
    for item in lst:
        for enter in item:
            f.write(str(enter))
            f.write(" ")
        f.write('\n')
    f.write('\n')

class BackTracker():
    class Board():
        def __init__(self, puzzle_arr, dom_arr, h_const, v_const, parent=None):
            self.puzzle = puzzle_arr # [[1,2,3],[3,2]]
            self.domains = dom_arr # list of list of sets [[{1,2,3,4,5},{},{}],[]]

            self.h_const = h_const
            self.v_const = v_const

            self.children = []
            self.parent = parent

            self.mrv_lst = []
            self.target = (0,0)
            self.target_vals = []
            self.target_index = 0
        
        def initialize(self):
            # initializes dom_arr to {1,2,3,4,5} for all cells
            self.domains = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]
            for row in range(5):
                for col in range(5):
                    self.domains[row][col] = {1,2,3,4,5}

        def isValid(self):
            # checks for empty set:
            for row in range(5):
                for col in range(5):
                    if self.puzzle[row][col]==0 and len(self.domains[row][col])==0:
                        return False
            # row column checking
            for row in self.puzzle:
                ith_row = set(row).discard(0)
                if ith_row == None: # if it only contains 0, that's fine
                    continue
                elif len(ith_row) != np.count_nonzero(row):
                    return False
            for col in range(5):
                col_length = set(self.puzzle[:,col]).discard(0) 
                if col_length == None: # if it only contains 0, that's fine
                    continue
                elif len(col_length) != np.count_nonzero(self.puzzle[:,col]):
                    return False
            
            # horizontal and vertical constraints checking
            for h_coord in self.h_const:
                right = (h_coord[0],h_coord[1]+1)
                left = h_coord
                ineq = self.h_const[h_coord]

                if self.puzzle[left[0]][left[1]]!=0 and self.puzzle[right[0]][right[1]]!=0:
                    if ineq == 1:
                        if self.puzzle[left[0]][left[1]] <= self.puzzle[right[0]][right[1]]:
                            return False
                    elif ineq == 0:
                        if self.puzzle[left[0]][left[1]] >= self.puzzle[right[0]][right[1]]:
                            return False

            for v_coord in self.v_const:
                up = v_coord
                down = (v_coord[0]+1,v_coord[1])
                ineq = self.v_const[v_coord]
                if self.puzzle[up[0]][up[1]]!=0 and self.puzzle[down[0]][down[1]]!=0:
                    if ineq == 1:
                        if self.puzzle[up[0]][up[1]] >= self.puzzle[down[0]][down[1]]:
                            return False
                    elif ineq == 0:
                        if self.puzzle[up[0]][up[1]] <= self.puzzle[down[0]][down[1]]:
                            return False
            return True

        def update(self):
            # updates domains
            # row column checking
            for row in range(5):
                for col in range(5):
                    curr = self.puzzle[row][col]
                    if curr!=0:
                        for i in range(5):
                            self.domains[row][i].discard(curr)
                        for j in range(5):
                            self.domains[j][col].discard(curr)

            # horizontal and vertical constraints checking
            for h_coord in self.h_const:
                right = (h_coord[0],h_coord[1]+1)
                left = h_coord
                ineq = self.h_const[h_coord]
                if self.puzzle[left[0]][left[1]]!=0 and self.puzzle[right[0]][right[1]]!=0: # skip if both assigned
                    continue
                elif self.puzzle[left[0]][left[1]]!=0: # if left assigned
                    if ineq == 1:
                        self.domains[right[0]][right[1]] -= set([i for i in range(self.puzzle[left[0]][left[1]],6)])
                    else:
                        self.domains[right[0]][right[1]] -= set([i for i in range(1,self.puzzle[left[0]][left[1]]+1)])
                
                elif self.puzzle[right[0]][right[1]]!=0: # if right assigned
                    if ineq == 1:
                        self.domains[left[0]][left[1]] -= set([i for i in range(1, self.puzzle[right[0]][right[1]]+1)])
                    else:
                        self.domains[left[0]][left[1]] -= set([i for i in range(self.puzzle[right[0]][right[1]],6)])
            for v_coord in self.v_const:
                up = v_coord
                down = (v_coord[0]+1,v_coord[1])
                ineq = self.v_const[v_coord]
                if self.puzzle[up[0]][up[1]]!=0 and self.puzzle[down[0]][down[1]]!=0: # skip if both assigned
                    continue
                elif self.puzzle[up[0]][up[1]]!=0: # if up assigned
                    if ineq == 1:
                        self.domains[down[0]][down[1]] -= set([i for i in range(1,self.puzzle[up[0]][up[1]]+1)])
                    else:
                        self.domains[down[0]][down[1]] -= set([i for i in range(self.puzzle[up[0]][up[1]],6)])
                
                elif self.puzzle[down[0]][down[1]]!=0: # if down assigned
                    if ineq == 1:
                        self.domains[up[0]][up[1]] -= set([i for i in range(self.puzzle[down[0]][down[1]],6)])
                    else:
                        self.domains[up[0]][up[1]] -= set([i for i in range(1,self.puzzle[down[0]][down[1]]+1)])


        def chooseTargetVal(self):
            mrv_lst = []
            least = 6 # keeps the shortest domains, i.e. the minimum remaining values
            for row in range(len(self.domains)):
                for col in range(len(self.domains[row])):
                    
                    if self.puzzle[row][col] != 0: # if already assigned, skip
                        continue
                    
                    curr_domain_len = len(self.domains[row][col])
                    if curr_domain_len < least:
                        least = curr_domain_len
                        mrv_lst = [(row,col)]
                    elif curr_domain_len == least:
                        mrv_lst.append((row,col))
            if len(mrv_lst) == 0: # shouldn't happen?
                print('MRV_lst has zero elements')
                pass
            
            elif len(mrv_lst) > 1:
                # degree heuristic
                degree_lst = [0]*len(mrv_lst)
                for i in range(len(mrv_lst)):
                    degree = 0
                    row,col = mrv_lst[i][0], mrv_lst[i][1]
                    # left
                    if col > 0:
                        if self.puzzle[row][col-1]==0:
                            degree+=1
                    # right
                    if col < 4:
                        if self.puzzle[row][col+1]==0:
                            degree+=1
                    # up
                    if row > 0:
                        if self.puzzle[row-1][col]==0:
                            degree+=1
                    # down
                    if row < 4:
                        if self.puzzle[row+1][col]==0:
                            degree+=1

                    degree_lst[i] = degree
                self.target = mrv_lst[degree_lst.index(max(degree_lst))]
            else:
                self.target = mrv_lst[0]
            self.target_vals = list(self.domains[self.target[0]][self.target[1]])


        def isComplete(self):
            return not (0 in self.puzzle)
    
    def __init__(self, initial_arr, initial_dom_arr, h_const, v_const):
        self.root = self.Board(initial_arr, initial_dom_arr, h_const, v_const)
    
    
    def solve(self):
        curr = self.root
        curr.initialize()
        curr.update()

        while True:
            # find the target to select values
            if curr.isComplete() and curr.isValid():
                return curr.puzzle

            # going down
            elif not curr.isComplete() and curr.isValid():
                curr.chooseTargetVal()
                new_puzzle = copy.deepcopy(curr.puzzle)
                new_domains = copy.deepcopy(curr.domains)
                new_insert_pos = curr.target
                new_puzzle[new_insert_pos[0]][new_insert_pos[1]] = curr.target_vals[curr.target_index]

                curr.children.append(self.Board(new_puzzle,new_domains,curr.h_const,curr.v_const,curr))
                curr = curr.children[curr.target_index]
                curr.update()
            
            elif not curr.isValid():
                curr = curr.parent
                while curr.target_index+1 >= len(curr.target_vals):
                    curr = curr.parent
                curr.target_index+=1


def gen_constraints(horiz, vert):
    HConstraints = {}
    VConstraints = {}
    constraint_dict = {'^' : 1,'>' : 1, '<' : 0, 'v' : 0}
    for line in range(len(horiz)):
        for i in range(len(horiz[line])):
            lin = horiz[line]
            if lin[i] in constraint_dict.keys():
                HConstraints[(line, i)] = constraint_dict[lin[i]]
    for line in range(len(vert)):
        for i in range(len(vert[line])):
            lin = vert[line]
            if lin[i] in constraint_dict.keys():
                VConstraints[(line, i)] = constraint_dict[lin[i]]
    return [HConstraints, VConstraints]

def printlst(lst, f):
    '''
    formatting the list to print out each item in the list
    '''
    for item in lst:
        for enter in item:
            f.write(str(enter))
            f.write(" ")
        f.write('\n')
    f.write('\n')

def main():
    parser = argparse.ArgumentParser(description='Futoshiki solver')
    parser.add_argument('--infile',type=argparse.FileType('r'),help='input file')
    parser.add_argument('--outfile',type=argparse.FileType('w'),help='output file')
    args = parser.parse_args()
    infile = args.infile.readlines()
    outfile = args.outfile

    lines = listify(infile)
    inpdata = lines[0:5]
    horiz = lines[6:11]
    vert = lines[12:17]

    test = np.array(inpdata)
    constraints = gen_constraints(horiz, vert)
    h_const = constraints[0]
    v_const = constraints[1]
    
    solver = BackTracker(test,[],h_const,v_const)
    solution = solver.solve()
    printlst(solution, outfile)
main()
