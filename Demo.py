import sensor, image, time, math, random

sensor.reset()
sensor.set_pixformat(sensor.RGB565) # grayscale is faster
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 2000)
clock = time.clock()

Board_Flag = False
red = [(28, 45, 10, 65, 13, 42)]
black = [(3, 21, -24, 19, -10, 18)]
white = [(52, 69, -15, 24, 1, 31)]
gray = [(38, 255)]
players = ['X', 'O']
board_roi = 0
# 棋盘基础坐标储存
base_board = [[' ' for _ in range(3)] for _ in range(3)]

draw_board = [[' ' for _ in range(3)] for _ in range(3)]


def draw_line(img, x0, y0, x1, y1, step=1):
    """计算两点组成的线段中每个点的坐标，可以优化只计算1/6，1/2，5/6几个点（为了绘制线所以全计算了）"""
    points = []
    if x0 == x1:
        for y in range(min(y0, y1), max(y0, y1)+1):
            points.append((x0, y))
    elif y0 == y1:
        for x in range(min(x0, x1), max(x0, x1)+1):
            points.append((x, y0))
    else:
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        if dx > dy :
            k = (y1 - y0) / (x1 - x0)
            b = y0 - k * x0
            if x0 > x1:
                for x in range(x1, x0+1, step):
                    y = int(k * x + b)
                    points.append((x, y))
            elif x0 < x1:
                for x in range(x0, x1+1, step):
                    y = int(k * x + b)
                    points.append((x, y))
#            points = sorted(points, key=lambda point: point[0])
        else:
            k = (x1 - x0) / (y1 - y0)
            b = x0 - k * y0
            if y0 > y1:
                for y in range(y1, y0+1, step):
                    x = int(k * y + b)
                    points.append((x, y))
            elif y0 < y1:
                for y in range(y0, y1+1, step):
                    x = int(k * y + b)
                    points.append((x, y))
#            points = sorted(points, key=lambda point: point[1])
    for point in points:
        img.set_pixel(point[0], point[1], (255, 0, 255))
    return points



def intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """输入四个坐标，计算前两个点组成的线段，后两个点组成的线段的交点坐标"""
    if x2 - x1 != 0 and x4 - x3 != 0:  # 都不垂直
        k1 = (y2 - y1) / (x2 - x1)
        b1 = y1 - k1 * x1

        k2 = (y4 - y3) / (x4 - x3)
        b2 = y3 - k2 * x3

        if k1 - k2 == 0:  # 平行无交点
            return None
        else:
            x = (b2 - b1) / (k1 - k2)
            y = k1 * x + b1
            return (int(x), int(y))
    elif x2 - x1 == 0 and x4 - x3 != 0:  # 第一条垂直
        k2 = (y4 - y3) / (x4 - x3)
        b2 = y3 - k2 * x3
        x = x1
        y = k2 * x + b2
        return (int(x), int(y))
    elif x2 - x1 != 0 and x4 - x3 == 0:  # 第二条垂直
        k1 = (y2 - y1) / (x2 - x1)
        b1 = y1 - k1 * x1
        x = x3
        y = k1 * x + b1
        return (int(x), int(y))
    else:  # 都垂直
        if x1 == x3:  # 同一条线
            return (x1, int((y1 + y2 + y3 + y4) / 4))  # 返回中点
        else:  # 平行无交点
            return (0, 0)



def find_max(blobs):
    max_size=0
    for blob in blobs:
        if blob[2]*blob[3] > max_size:
            max_blob=blob
            max_size = blob[2]*blob[3]
    return max_blob

def find_black_qizi(imgs):
    global board_roi, draw_board
    """查找黑色棋子"""
    imgs = imgs.binary(black)
    # 开操作处理
    imgs = imgs.open(3)
    blobs = imgs.find_blobs(gray,roi=board_roi)
    if blobs:
        for blob in blobs:
#            img.draw_cross((blob.cx(), blob.cy()), color=( 0, 255, 255))
#            img.draw_rectangle(blob[0:4], (0, 0, 255), 2) #rect #用矩形标记出目标颜色
            (x,y) = find_closest_point(base_board, (blob.cx(), blob.cy()))
            make_move(draw_board, x, y, "X")

def find_white_qizi(imgs):
    global board_roi, draw_board
    """查找白色棋子"""
    imgs = imgs.binary(white)
    # 开操作处理
#    imgs = imgs.close(3)
    blobs = imgs.find_blobs(gray,roi=board_roi, area_threshold=100)
    if blobs:
        for blob in blobs:
#            img.draw_cross((blob.cx(), blob.cy()), color=( 0, 255, 255))
#            img.draw_rectangle(blob[0:4], (255, 0, 255), 2) #rect #用矩形标记出目标颜色
            (x,y) = find_closest_point(base_board, (blob.cx(), blob.cy()))
            make_move(draw_board, x, y, "O")

def find_qipan(imgs):
    global Board_Flag, base_board, board_roi
    """查找棋盘"""
    imgs = imgs.binary(red)
    # 闭操作处理,去除黑线格子干扰
    imgs = imgs.close(3)
    try:
        for r in imgs.find_rects( threshold = 10000):

            img.draw_rectangle(r.rect(), color = (255, 255, 0))
            # 更新ROI区域为后续棋子识别做准备
            (x, y, w, h) = r.rect()
            board_roi = (x+10, y+10, w-10, h-10)
            a1_list=draw_line(img, r.corners()[0][0],r.corners()[0][1],r.corners()[3][0],r.corners()[3][1])
            a2_list=draw_line(img, r.corners()[3][0],r.corners()[3][1],r.corners()[2][0],r.corners()[2][1])
            a3_list=draw_line(img, r.corners()[2][0],r.corners()[2][1],r.corners()[1][0],r.corners()[1][1])
            a4_list=draw_line(img, r.corners()[1][0],r.corners()[1][1],r.corners()[0][0],r.corners()[0][1])

# 左上角点
#            img.draw_cross((r.corners()[2][0], r.corners()[2][1]), color=( 0, 255, 255))

#    # 列
##            draw_line(img, a1_list[len(a1_list)//6][0],a1_list[len(a1_list)//6][1],a3_list[len(a3_list)//6][0],a3_list[len(a3_list)//6][1])
#    #        draw_line(img, a1_list[3*len(a1_list)//6][0],a1_list[3*len(a1_list)//6][1],a3_list[3*len(a3_list)//6][0],a3_list[3*len(a3_list)//6][1])
#    #        draw_line(img, a1_list[5*len(a1_list)//6][0],a1_list[5*len(a1_list)//6][1],a3_list[5*len(a3_list)//6][0],a3_list[5*len(a3_list)//6][1])

#    # 行
##            draw_line(img, a2_list[len(a2_list)//6][0],a2_list[len(a2_list)//6][1],a4_list[len(a4_list)//6][0],a4_list[len(a4_list)//6][1])
#    #        draw_line(img, a2_list[3*len(a2_list)//6][0],a2_list[3*len(a2_list)//6][1],a4_list[3*len(a4_list)//6][0],a4_list[3*len(a4_list)//6][1])
#    #        draw_line(img, a2_list[5*len(a2_list)//6][0],a2_list[5*len(a2_list)//6][1],a4_list[5*len(a4_list)//6][0],a4_list[5*len(a4_list)//6][1])


            x, y = intersection(a1_list[len(a1_list)//6][0],a1_list[len(a1_list)//6][1],a3_list[len(a3_list)//6][0],a3_list[len(a3_list)//6][1], a2_list[len(a2_list)//6][0],a2_list[len(a2_list)//6][1],a4_list[len(a4_list)//6][0],a4_list[len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "1", color=( 0, 255, 255))
            base_board[0][0] = (x, y)
            x, y = intersection(a1_list[3*len(a1_list)//6][0],a1_list[3*len(a1_list)//6][1],a3_list[3*len(a3_list)//6][0],a3_list[3*len(a3_list)//6][1], a2_list[len(a2_list)//6][0],a2_list[len(a2_list)//6][1],a4_list[len(a4_list)//6][0],a4_list[len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "2", color=( 0, 255, 255))
            base_board[0][1] = (x, y)
            x, y = intersection(a1_list[5*len(a1_list)//6][0],a1_list[5*len(a1_list)//6][1],a3_list[5*len(a3_list)//6][0],a3_list[5*len(a3_list)//6][1], a2_list[len(a2_list)//6][0],a2_list[len(a2_list)//6][1],a4_list[len(a4_list)//6][0],a4_list[len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "3", color=( 0, 255, 255))
            base_board[0][2] = (x, y)

            x, y = intersection(a1_list[len(a1_list)//6][0],a1_list[len(a1_list)//6][1],a3_list[len(a3_list)//6][0],a3_list[len(a3_list)//6][1], a2_list[3*len(a2_list)//6][0],a2_list[3*len(a2_list)//6][1],a4_list[3*len(a4_list)//6][0],a4_list[3*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "4", color=( 0, 255, 255))
            base_board[1][0] = (x, y)
            x, y = intersection(a1_list[3*len(a1_list)//6][0],a1_list[3*len(a1_list)//6][1],a3_list[3*len(a3_list)//6][0],a3_list[3*len(a3_list)//6][1], a2_list[3*len(a2_list)//6][0],a2_list[3*len(a2_list)//6][1],a4_list[3*len(a4_list)//6][0],a4_list[3*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "5", color=( 0, 255, 255))
            base_board[1][1] = (x, y)
            x, y = intersection(a1_list[5*len(a1_list)//6][0],a1_list[5*len(a1_list)//6][1],a3_list[5*len(a3_list)//6][0],a3_list[5*len(a3_list)//6][1], a2_list[3*len(a2_list)//6][0],a2_list[3*len(a2_list)//6][1],a4_list[3*len(a4_list)//6][0],a4_list[3*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "6", color=( 0, 255, 255))
            base_board[1][2] = (x, y)

            x, y = intersection(a1_list[len(a1_list)//6][0],a1_list[len(a1_list)//6][1],a3_list[len(a3_list)//6][0],a3_list[len(a3_list)//6][1], a2_list[5*len(a2_list)//6][0],a2_list[5*len(a2_list)//6][1],a4_list[5*len(a4_list)//6][0],a4_list[5*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "7", color=( 0, 255, 255))
            base_board[2][0] = (x, y)
            x, y = intersection(a1_list[3*len(a1_list)//6][0],a1_list[3*len(a1_list)//6][1],a3_list[3*len(a3_list)//6][0],a3_list[3*len(a3_list)//6][1], a2_list[5*len(a2_list)//6][0],a2_list[5*len(a2_list)//6][1],a4_list[5*len(a4_list)//6][0],a4_list[5*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "8", color=( 0, 255, 255))
            base_board[2][1] = (x, y)
            x, y = intersection(a1_list[5*len(a1_list)//6][0],a1_list[5*len(a1_list)//6][1],a3_list[5*len(a3_list)//6][0],a3_list[5*len(a3_list)//6][1], a2_list[5*len(a2_list)//6][0],a2_list[5*len(a2_list)//6][1],a4_list[5*len(a4_list)//6][0],a4_list[5*len(a4_list)//6][1])
            img.draw_cross((x, y), color=( 0, 255, 255))
            img.draw_string(x, y, "9", color=( 0, 255, 255))
            base_board[2][2] = (x, y)

            Board_Flag = True
    except Exception  as e:
        pass

def print_board(board):
    """打印棋盘内容"""
    for row in board:
        print("|".join(row))
    print()


def find_empty_location(board):
    """找到棋盘上的一个空位置，如果中心可用则返回中心，否则随机返回一个空位置"""
    empty_locations = [(i, j) for i in range(3) for j in range(3) if board[i][j] == ' ']
    if (1, 1) in empty_locations:  # 中心位置
        return (1, 1)
    if empty_locations:
        return random.choice(empty_locations)
    return None  # 如果没有空位则返回None（理论上不应该发生）

# 辅助函数，用于生成棋盘的所有可能下一步
def generate_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == ' ':
                moves.append((i, j))
    return moves

def find_best_move(board, player):
    # 穷举法开始
    best_move = None
    opponent = 'O' if player == 'X' else 'X'
    # 生成所有可能的下一步
    moves = generate_moves(board)

    # 遍历所有可能的下一步
    for move in moves:
        # 复制棋盘并尝试当前棋步
        temp_board = [row[:] for row in board]  # 使用列表推导式和切片进行深拷贝
        temp_board[move[0]][move[1]] = player
        # 评估当前棋步的结果
        outcome = check_winner(temp_board)
        # 更新最佳棋步和最佳结果
        if outcome == player:
            # 如果AI获胜，则立即返回该棋步
            return move

    # 如果没有找到胜利的棋步，则去寻找能阻止人类获胜的棋步
    for move in moves:
        # 复制棋盘并尝试当前棋步
        temp_board = [row[:] for row in board]  # 使用列表推导式和切片进行深拷贝
        temp_board[move[0]][move[1]] = opponent
        # 评估当前棋步的结果
        outcome = check_winner(temp_board)
        # 更新最佳棋步和最佳结果
        if outcome == opponent:
            # 如果AI获胜，则立即返回该棋步
            return move

    # 如果没有找到导致AI获胜的棋步，也无最佳防御棋步，则随机返回一个空位置
    best_move = find_empty_location(board)
    return best_move

def make_move(board, row, col, player):
    """在棋盘上放置棋子"""
    board[row][col] = player

def check_winner(board):
    """检查是否有玩家获胜"""
    # 检查行
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != ' ':
            return row[0]
    # 检查列
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != ' ':
            return board[0][col]
    # 检查对角线
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != ' ':
        return board[0][2]
    # 没有获胜者
    return None


def find_closest_point(points, target):
    """返回与棋盘坐标最近的索引"""
    min_distance = float('inf')
    closest_index = None
    for i in range(len(points)):
        for j in range(len(points[i])):
            point = points[i][j]
            distance = math.sqrt((point[0] - target[0])**2 + (point[1] - target[1])**2)
            if distance < min_distance:
                min_distance = distance
                closest_index = (i, j)
    return closest_index


while(True):
    clock.tick()
    img = sensor.snapshot()
    imgs = img.copy()

# 找到棋盘后找棋子
#    if Board_Flag:
#        find_black_qizi(imgs)
#        img = sensor.snapshot()
#        imgs = img.copy()
#        find_white_qizi(imgs)
#    else:
#        find_qipan(imgs)

# 找棋盘
    find_qipan(imgs)

    print_board(draw_board)
