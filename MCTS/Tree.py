import MCTS.Node as Node
import Support.Board_Stack as BS
from Support.OneHotEncoding import OneHotEncode as OHE

class Tree:

    def __init__(self,PN): # 체스보드의 현재 상태를 입력받아 board_stack에 전달
        self.root_Node = None
        self.currentNode = None#현재 가리키는 노드를 임시로 저장
        self.board_stack = None #MCTS에서 각노드의 명령어를 사용할 Board_Stack
        self.policyNetwork = PN
        self.ohe = OHE()

    def reset_board(self,Board):
        self.board_stack = BS.Board_Stack(Board)
        self.set_RootNode()
    def inherit_tree(self, move):
        child = self.root_Node.find_move(move)
        self.board_stack.stack_push(move)
        try :
            child.del_parent()
            self.root_Node = child
            self.currentNode = self.root_Node
            print("상속완료")
        except :
            self.reset_board(self.board_stack.get_ChessBoard())
            print("상속 실패")
    def set_RootNode(self):
        self.root_Node = Node.Node(None,None,self.board_stack.get_Color()) # 루트 노드 생성
        self.currentNode = self.root_Node #루트노드가 생성될 때 currentNode로 설정

    def go_root(self,Board):
        self.currentNode = self.root_Node
        del self.board_stack
        self.board_stack = BS.Board_Stack(Board)
    def go_next(self):
        self.currentNode = self.currentNode.get_bestChild()
        self.currentNode.add_Visit(1)
        self.board_stack.stack_push(self.currentNode.command)
    def go_parrent(self):
        self.currentNode = self.currentNode.get_Parent()
        self.board_stack.stack_pop()

    def set_BoardString(self,boardString):
        self.boardString = boardString

    def get_CurrentNode(self):#현재 tree가 가리키고 있는 노드 반환
        return self.currentNode

    #Board_Stack에 추가할 command를 갱신해야 함
    def set_CurrentNode(self ,node):#들어온 node를 currentNode로
        self.currentNode = node

    def add_ChildNode(self,node): #tree에서 currentNode에 자식 추가
        self.currentNode.add_ChildNode(node)

    def expand_RL_PolicyNetwork(self):
        tmpBoard = self.board_stack.get_ChessBoard()
        turn =tmpBoard.turn

        ###### 강화학습된 정책망을 이용하여 확장하기 ########
        ### 추후에 강화학습 학습 후 expandedChild에 삽입 ###
        expandedChild = None
        expandedChild.set_Color(not turn)
        self.currentNode.add_ChildNode(expandedChild)
        self.tree.set_CurrentNode(expandedChild)

    # policy
    def makeNextChildByPolicyNetwork(self):

        if not self.currentNode.is_array4096():
            tmpBoard = self.board_stack.get_ChessBoard()
            array4096, argmaxOfSoftmax = self.policyNetwork.getArraysOfPolicyNetwork(tmpBoard)
            self.currentNode.set_array4096(array4096)
            self.currentNode.set_argmaxOfSoftmax(argmaxOfSoftmax)

        madeNode = self.get_BestQuNode()
        # q+u 값을 최대화하는 노드 선택

        if not self.currentNode.is_child(madeNode):
            #자식 노드가 아닌 경우에만 자식으로 추가
            self.currentNode.add_ChildNode(madeNode)

        self.currentNode.renewForSelection()
        self.set_CurrentNode(madeNode)
        self.currentNode.add_Visit(1)
        # print(self.board_stack.get_ChessBoard().turn)
        # print(self.board_stack.get_ChessBoard())
        self.board_stack.stack_push(madeNode.get_Command())

    def get_BestQuNode(self):
        #Qu는 가장 Q(s,a) + u(s,a) 의 값
        #자식 노드의 수 다음 배열에서 Node를 만들어서
        argmaxOfSoftmax = self.currentNode.get_argmaxOfSoftmax()
        array4096 = self.currentNode.get_array4096()
        index = argmaxOfSoftmax[self.currentNode.get_LengthOfChild()]
        command = self.ohe.indexToMove4096(index)
        color = not self.currentNode.get_Color()

        newNode = Node.Node(self.currentNode, command, array4096[index], color)

        childList = self.currentNode.get_Child()
        if len(childList) == 0: #자식이 없는 경우
            return newNode
        maxQuNode = newNode

        for node in childList:
            if node.get_Qu() > maxQuNode.get_Qu():
                maxQuNode = node

        ####is_child만으로는 중복 생성되는 노드를 막을 수 없음. 수정 필요
        if self.currentNode.is_child(maxQuNode):
            #자식인경우 새로 생성된 newNode는 사용되지 않았으므로
            #소멸
            del newNode

        return maxQuNode

    def get_RootNode(self):
        return self.root_Node
    def get_GameOver(self):
        return self.board_stack.get_GameOver() #게임종료를 True False로 반환
    def translatedResult(self):
        rm = {'1-0': 1, '0-1': -1, '1/2-1/2': 0, '*': 0}
        # 게임의 끝, ( 백승 = 1, 흑승 = -1, 무승부, 0 )
        result = self.board_stack.get_Result()
        convertedResult = rm[result]
        return convertedResult
    def get_currentBoard(self):
        return self.board_stack.get_ChessBoard()

    def check_board(self,board):
        flag = False
        if board.can_claim_threefold_repetition():
            flag = True

        if board.can_claim_fifty_moves():
            flag = True
        if board.can_claim_draw():
            flag = True

        if board.is_fivefold_repetition():
            flag = True

        if board.is_seventyfive_moves():
            flag = True
        return flag