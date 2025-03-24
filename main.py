import pygame
import math

class GameObject:
	PADDLE = 10
	BALL = 20
	BRICK = 30

	def __init__(self, id: int, gameInstance: "Game"):
		self.gameInstance = gameInstance
		self.id = id
		self.deallocate = False
	
	def Update(self):
		pass

	def Render(self):
		pass

	def GetID(self):
		return self.id

	def CheckDeallocate(self):
		pass

"""
PhysicsGameObjects have different ways to store dimensions depending if
they're a circle or a rect. Currently they're stored in the immediate
inheriters of the class, but would a PhysicsRect and PhysicsCircle
that inherit from PhysicsGameObject be an improvement or overengineered?
"""
class PhysicsGameObject(GameObject):
	def __init__(self, id: int, gameInstance: "Game"):
		GameObject.__init__(self, id, gameInstance)
		self.pos = [0.0, 0.0]
		self.velocity = [0.0, 0.0]
		self.acceleration = [0.0, 0.0]
	
	def PushVelocity(self):
		self.pos = [self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1]]
	
	def AccelerateToLimit(self, limit: float):
		self.velocity = [self.velocity[0] + self.acceleration[0], self.velocity[1] + self.acceleration[1]]
		self.velocity = [Utility.minValue(limit, self.velocity[0]), Utility.minValue(limit, self.velocity[1])]
		self.velocity = [Utility.maxValue(-limit, self.velocity[0]), Utility.maxValue(-limit, self.velocity[1])]
	
	def AggressiveAccelerateToLimit(self, limit: float, change: float):
		# change applies different acceleration if the body is changing from one direction to another until it passes 0

		#ideally I would like this to be written without nested checks to work more like a math function
		if self.acceleration[0] > 0:
			if self.velocity[0] < 0:
				self.velocity[0] = Utility.minValue(limit, self.velocity[0] + self.acceleration[0] * change)
			else:
				self.velocity[0] = Utility.minValue(limit, self.velocity[0] + self.acceleration[0])
		elif self.acceleration[0] < 0:
			if self.velocity[0] > 0:
				self.velocity[0] = Utility.maxValue(-limit, self.velocity[0] + self.acceleration[0] * change)
			else:
				self.velocity[0] = Utility.maxValue(-limit, self.velocity[0] + self.acceleration[0])

		if self.acceleration[1] > 0:
			if self.velocity[1] < 0:
				self.velocity[1] = Utility.minValue(limit, self.velocity[1] + self.acceleration[1] * change)
			else:
				self.velocity[1] = Utility.minValue(limit, self.velocity[1] + self.acceleration[1])
		elif self.acceleration[1] < 0:
			if self.velocity[1] > 0:
				self.velocity[1] = Utility.maxValue(-limit, self.velocity[1] - self.acceleration[1] * change)
			else:
				self.velocity[1] = Utility.maxValue(-limit, self.velocity[1] - self.acceleration[1])
	
	def DragToZero(self, intensity: float):
		#cutoff means set to 0
		if self.velocity[0] > 0.0:
			self.velocity[0] = Utility.maxValue(0.0, self.velocity[0] - intensity)
		elif self.velocity[0] < 0.0:
			self.velocity[0] = Utility.minValue(0.0, self.velocity[0] + intensity)

		if self.velocity[1] > 0.0:
			self.velocity[1] = Utility.maxValue(0.0, self.velocity[1] - intensity)
		elif self.velocity[1] < 0.0:
			self.velocity[1] = Utility.minValue(0.0, self.velocity[1] + intensity)
	
	def GetCollisionShape(self):
		pass


#pygame don't have a circle so I'll handle it
class CircleCollider:
	def __init__(self, pos: list[float, float], radius: float):
		# no reference to pos
		self.pos = [pos[0], pos[1]]
		self.radius = radius
	
	def CircleCollide(self, circle: "CircleCollider"):
		d = Utility.distance(self.pos, circle.pos)
		return d < self.radius+circle.radius
	
	def RectCollide(self, rect: "pygame.Rect"):
		pos = [self.pos[0], self.pos[1]]
		pos[0] = Utility.maxValue(pos[0], rect.left)
		pos[0] = Utility.minValue(pos[0], rect.right)
		pos[1] = Utility.maxValue(pos[1], rect.top)
		pos[1] = Utility.minValue(pos[1], rect.bottom)
		return Utility.distance(pos, self.pos) < self.radius
	
	def GetRectCollisionSide(self, rect: "pygame.Rect"):
		pos = [self.pos[0], self.pos[1]]
		pos[0] = Utility.maxValue(pos[0], rect.left)
		pos[0] = Utility.minValue(pos[0], rect.right)
		pos[1] = Utility.maxValue(pos[1], rect.top)
		pos[1] = Utility.minValue(pos[1], rect.bottom)

		return [
			-1 if pos[0] == rect.left else (1 if pos[0] == rect.right else 0),
			-1 if pos[1] == rect.top else (1 if pos[1] == rect.bottom else 0)
		]


class Paddle(PhysicsGameObject):
	def __init__(self, gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.PADDLE, gameInstance)


		self.pos = [gameInstance.dim[0]/2+20, gameInstance.dim[1]*15/16]
		self.dim = [100, 10]
		self.maxMoveSpeed = 10
		self.accelerationSpeed = 1
		self.accelerationBrakeSpeed = 2

		self.reflectionIntensity = 30

	def GetCollisionShape(self):
		return pygame.Rect(
			self.pos[0] - self.dim[0]/2,
			self.pos[1] - self.dim[1]/2,
			self.dim[0],
			self.dim[1]
		)

	def Update(self):
		self.PushVelocity()
		self.AggressiveAccelerateToLimit(self.maxMoveSpeed, self.accelerationBrakeSpeed)
		
		if self.gameInstance.controller.LEFT:
			self.acceleration[0] = -self.accelerationSpeed
		elif self.gameInstance.controller.RIGHT:
			self.acceleration[0] = self.accelerationSpeed
		else:
			self.acceleration[0] = 0.0
			self.DragToZero(2.0)

	def Render(self):
		pygame.draw.rect(self.gameInstance.window, (255, 255, 255), [self.pos[0] - self.dim[0]/2, self.pos[1] - self.dim[1]/2, self.dim[0], self.dim[1]])


#this could be fully implemented in a challenge mode
class CurvyPaddle(PhysicsGameObject):
	def __init__(self, gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.PADDLE, gameInstance)
		self.pos = [gameInstance.dim[0]/2, gameInstance.dim[1]]
		self.paddleAngle = 35 # value between 45 and 135
		self.paddleThickness = 16
		self.paddleDiameter = 200
		self.maxMoveSpeed = 10
		self.accelerationSpeed = 1
		self.accelerationBrakeSpeed = 2
	
	def GetVectorToBall(self, ball: "Ball"):
		pos = [ball.pos[0], ball.pos[1]]
		pos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]
		d = math.sqrt(pos[0]*pos[0] + pos[1]*pos[1])
		return [pos[0] / d, pos[1] / d]
	
	def GetRotatedVectorToBall(self, ball: "Ball"):
		pos = [ball.pos[0], ball.pos[1]]
		pos = [pos[0] - self.pos[0], pos[1] - self.pos[1]]
		d = math.sqrt(pos[0]*pos[0] + pos[1]*pos[1])
		return [-pos[1] / d, pos[0] / d]
	
	def GetCollisionShape(self) -> CircleCollider:
		return CircleCollider(self.pos, self.paddleDiameter/2)
	
	def HasValidCollisionWithBall(self, ball: "Ball"):
		paddleCollider = self.GetCollisionShape()
		ballCollider = ball.GetCollisionShape()
		vec = self.GetVectorToBall(ball)
		angle = math.atan2(-vec[1], vec[0])*180.0/3.14159265 - 90.0
		distance = Utility.distance(self.pos, ball.pos)

		if ballCollider.CircleCollide(paddleCollider) and abs(angle) < self.paddleAngle and distance > self.paddleDiameter/2-self.paddleThickness and ball.velocity[1] > 0:
			return True
		
		return False

	def Update(self):
		self.PushVelocity()
		self.AggressiveAccelerateToLimit(self.maxMoveSpeed, self.accelerationBrakeSpeed)
		
		if self.gameInstance.controller.LEFT:
			self.acceleration[0] = -self.accelerationSpeed
		elif self.gameInstance.controller.RIGHT:
			self.acceleration[0] = self.accelerationSpeed
		else:
			self.acceleration[0] = 0.0
			self.DragToZero(2.0)
	
	def Render(self):
		paddleVector = [math.sin(Utility.angleToRandian(self.paddleAngle)), math.cos(Utility.angleToRandian(self.paddleAngle))]

		triangleSize = math.sqrt(self.paddleDiameter*self.paddleDiameter/2)+2

		leftTriangleTop = [-paddleVector[0]*(triangleSize)+self.pos[0], -paddleVector[1]*(triangleSize)+self.pos[1]]
		leftTriangleBottom = [-paddleVector[1]*(triangleSize)+self.pos[0], paddleVector[0]*(triangleSize)+self.pos[1]]

		rightTriangleTop = [paddleVector[0]*(triangleSize)+self.pos[0], -paddleVector[1]*(triangleSize)+self.pos[1]]
		rightTriangleBottom = [paddleVector[1]*(triangleSize)+self.pos[0], paddleVector[0]*(triangleSize)+self.pos[1]]

		leftEdge = [-paddleVector[0]*(self.paddleDiameter/2-self.paddleThickness/2) + self.pos[0], -paddleVector[1]*(self.paddleDiameter/2-self.paddleThickness/2) + self.pos[1]]
		rightEdge = [paddleVector[0]*(self.paddleDiameter/2-self.paddleThickness/2) + self.pos[0], -paddleVector[1]*(self.paddleDiameter/2-self.paddleThickness/2) + self.pos[1]]

		hideColor = self.gameInstance.backgroundColor

		pygame.draw.ellipse(
			self.gameInstance.window,
			(255, 255, 255),
			[
				self.pos[0]-self.paddleDiameter/2,
				self.pos[1]-self.paddleDiameter/2,
				self.paddleDiameter,
				self.paddleDiameter
			]
		)
		pygame.draw.ellipse(
			self.gameInstance.window,
			hideColor,
			[
				self.pos[0]-self.paddleDiameter/2+self.paddleThickness,
				self.pos[1]-self.paddleDiameter/2+self.paddleThickness,
				(self.paddleDiameter-self.paddleThickness*2),
				(self.paddleDiameter-self.paddleThickness*2)
			]
		)
		if self.paddleAngle < 90:
			pygame.draw.rect(self.gameInstance.window, hideColor, [self.pos[0]-self.paddleDiameter/2, self.pos[1], self.paddleDiameter, self.paddleDiameter/2])
		pygame.draw.polygon(self.gameInstance.window, hideColor, [leftTriangleTop, self.pos, leftTriangleBottom])
		pygame.draw.polygon(self.gameInstance.window, hideColor, [rightTriangleBottom, self.pos, rightTriangleTop])
		pygame.draw.circle(self.gameInstance.window, (255, 255, 255), leftEdge, self.paddleThickness/2)
		pygame.draw.circle(self.gameInstance.window, (255, 255, 255), rightEdge, self.paddleThickness/2)


class Brick(PhysicsGameObject):
	defaultDim = (60, 20)

	def __init__(self, pos: list[float, float], gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.BRICK, gameInstance)
		self.pos = [pos[0], pos[1]]
		self.dim = [Brick.defaultDim[0], Brick.defaultDim[1]]
	
	def GetCollisionShape(self):
		return pygame.Rect(
			self.pos[0] - self.dim[0]/2,
			self.pos[1] - self.dim[1]/2,
			self.dim[0],
			self.dim[1]
		)

	def Update(self):
		pass

	def Render(self):
		pygame.draw.rect(self.gameInstance.window, (255, 255, 255), [self.pos[0] - self.dim[0]/2, self.pos[1] - self.dim[1]/2, self.dim[0], self.dim[1]])


class Ball(PhysicsGameObject):
	def __init__(self, gameInstance: "Game"):
		PhysicsGameObject.__init__(self, GameObject.BALL, gameInstance)
		self.velocity = [0.0, 0.0]
		self.moveSpeed = 3
		self.radius = 6
	
	def SetDirection(self, relativePosition: list[float, float]):
		d = math.sqrt(relativePosition[0]*relativePosition[0]+relativePosition[1]*relativePosition[1])
		self.velocity = [relativePosition[0]/d*self.moveSpeed, relativePosition[1]/d*self.moveSpeed]
	
	#unused
	def GetReverseVelocityVector(self):
		d = math.sqrt(self.velocity[0]*self.velocity[0]+self.velocity[1]*self.velocity[1])
		return [self.velocity[0]/d, self.velocity[1]/d]

	def GetCollisionShape(self) -> CircleCollider:
		return CircleCollider(self.pos, self.radius)

	# grabbing objects from a general array means that pylance doesn't provide hints
	# I thought about switching collision checking to paddle and bricks, but doing it this way creates fewer checks
	def CheckCollisions(self):
		for obj in self.gameInstance.instance:
			if obj.id == GameObject.PADDLE:
				circle = self.GetCollisionShape()
				rect = obj.GetCollisionShape()
				if circle.RectCollide(rect) and self.velocity[1] > 0:
					direction = [self.pos[0] - obj.pos[0], self.pos[1] - (obj.pos[1]+100/obj.reflectionIntensity)]
					self.SetDirection(direction)
			elif obj.id == GameObject.BRICK:
				circle = self.GetCollisionShape()
				rect = obj.GetCollisionShape()
				if circle.RectCollide(rect) and obj.deallocate == False:
					obj.deallocate = True
					sides = circle.GetRectCollisionSide(rect)
					if sides[0] != 0:
						self.velocity[0] = -self.velocity[0]
					if sides[1] != 0:
						self.velocity[1] = -self.velocity[1]

	def Update(self):
		self.pos = [self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1]]

		if self.velocity[0] > 0 and self.pos[0]+self.radius > self.gameInstance.dim[0]:
			self.velocity[0] = -self.velocity[0]
		elif self.velocity[0] < 0 and self.pos[0] - self.radius < 0:
			self.velocity[0] = -self.velocity[0]

		elif self.velocity[1] < 0 and self.pos[1] - self.radius < 0:
			self.velocity[1] = -self.velocity[1]

		self.CheckCollisions()

	def Render(self):
		pygame.draw.circle(self.gameInstance.window, (255, 255, 255), self.pos, self.radius)


class Controller:
	def __init__(self):
		self.LEFT = False
		self.RIGHT = False
		self.ACTION = False


class Utility:
	def angleToRandian(n: float):
		return n*math.pi/180

	def minValue(a, b):
		return a if a < b else b

	def maxValue(a, b):
		return a if a > b else b

	def distance(pos1: list[float, float], pos2: list[float, float]):
		return math.sqrt((pos1[0]-pos2[0])*(pos1[0]-pos2[0])+(pos1[1]-pos2[1])*(pos1[1]-pos2[1]))

	def NormalizeVector(vec: list[float, float]):
		d = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
		return [vec[0]/d, vec[1]/d]

	def VectorMultiply(vec1: list[float, float], vec2: list[float, float]):
		vec3 = [vec1[0]*vec2[0]-vec1[1]+vec2[1], vec1[0]*vec2[1]+vec1[1]*vec2[0]]
		return Utility.NormalizeVector(vec3)

class Game:
	def __init__(self):
		self.window = None
		self.running = True
		self.dim = (800, 800)

		self.controller = Controller()

		self.instance = []

		self.gameTime = 0

		self.backgroundColor = (100, 100, 100)

	def Start(self):

		#paddle and ball were added to game isntance for debugging, but they don't need to be here
		self.paddle = Paddle(self)
		self.ball = Ball(self)

		self.ball = Ball(self)
		self.ball.pos = [self.dim[0]/2, 500]
		self.ball.SetDirection([0.0, 1.0])

		self.instance.append(self.paddle)
		self.instance.append(self.ball)

		#this will eventually be moved to a level instance to allow for loading levels

		topMargin = 10
		bottomMargin = 350
		leftMargin = 40
		rightMargin = 40

		verticalSpacing = 10
		horizontalSpacing = 10

		# this implementation for a level generator is janky and causes weird spacing
		for y in range(int(Brick.defaultDim[1]/2 + topMargin), int(self.dim[1] - Brick.defaultDim[1]/2 - bottomMargin), int(verticalSpacing + Brick.defaultDim[1])):
			for x in range(int(Brick.defaultDim[0]/2 + leftMargin), int(self.dim[0] - Brick.defaultDim[0]/2 - rightMargin), int(horizontalSpacing + Brick.defaultDim[0])):
				self.instance.append(Brick([x, y], self))
	
	def Input(self):
		for e in pygame.event.get():
			if e.type == pygame.QUIT:
				self.running = False
			elif e.type == pygame.KEYDOWN:
				if e.key == pygame.K_a or e.key == pygame.K_LEFT:
					self.controller.LEFT = True
				elif e.key == pygame.K_d or e.key == pygame.K_RIGHT:
					self.controller.RIGHT = True
			elif e.type == pygame.KEYUP:
				if e.key == pygame.K_a or e.key == pygame.K_LEFT:
					self.controller.LEFT = False
				elif e.key == pygame.K_d or e.key == pygame.K_RIGHT:
					self.controller.RIGHT = False

	def Update(self):
		for obj in self.instance:
			obj.Update()
		
		for i in range(len(self.instance)-1, -1, -1):
			obj = self.instance[i]
			if obj.deallocate:
				self.instance.remove(obj)

	def Render(self):
		self.window.fill(self.backgroundColor)

		for obj in self.instance:
			obj.Render()

		pygame.display.flip()

	def main(self):
		pygame.init()

		self.window = pygame.display.set_mode(self.dim)

		tps = 60.0
		ns = 1000.0 / tps
		actualTPS = 0

		delta = 0.0

		lastTime = pygame.time.get_ticks()

		fps = 144.0
		frameNS = 1000.0 / fps
		actualFPS = 0

		lastFrame = pygame.time.get_ticks()

		timer = pygame.time.get_ticks()

		reportRefreshRate = False

		self.Start()

		while self.running:
			self.Input()

			nowTime = pygame.time.get_ticks()
			delta += float(nowTime-lastTime) / ns
			lastTime = nowTime

			while not (delta < 1):
				self.Update()
				self.gameTime += 1
				actualTPS += 1
				delta -= 1.0
			
			nowFrame = pygame.time.get_ticks()
			if float(nowFrame-lastFrame) > frameNS:
				lastFrame = nowFrame
				self.Render()
				actualFPS += 1
			
			nowTimer = pygame.time.get_ticks()
			if nowTimer - timer > 1000:
				timer = nowTimer
				if reportRefreshRate:
					print(f"TPS: {actualTPS}\nFPS: {actualFPS}")
				actualTPS = 0
				actualFPS = 0

		pygame.quit()


if __name__ == "__main__":
	g = Game()
	g.main()
