from ezblock import PWM, Servo
import time
import math
import os
from ezblock import fileDB

def check_file(dir:str):
    if not os.path.exists(dir.rsplit('/',1)[0]):
        try:
            os.makedirs(dir.rsplit('/',1)[0])
            f = open(dir,'w')
            f.close
        except Exception as e:
            print(e)

class Robot():
    move_list = {}
    PINS = [None, "P0","P1","P2","P3","P4","P5","P6","P7","P8","P9","P10","P11"]
    # PINS = [None, "D0","D1","D2","D3","D6","D7","A8","A9","A10","A11","A12","A13"]
    def __init__(self, pin_list, group=4, db='/opt/ezblock/.config',name=None, init_angles=None):

        self.servo_list = []
        self.pin_num = len(pin_list)
        self.list_name = name


        check_file(db)
        if self.list_name == None:
            if self.pin_num == 12:
                self.list_name = 'spider_servo_offset_list'
            elif self.pin_num == 3:
                self.list_name = 'piarm_servo_offset_list'
            elif self.pin_num == 4:
                self.list_name = 'sloth_servo_offset_list'
            elif self.pin_num == 8:
                self.list_name = 'pidog_servo_offset_list'
            else:
                self.list_name = 'other'

        # offset
        self.db = fileDB(db=db)
        temp = self.db.get(self.list_name, default_value=str(self.new_list(0)))
        temp = [float(i.strip()) for i in temp.strip("[]").split(",")]
        # check
        if len(temp) == self.pin_num:
            self.offset = temp
        else:
            print('\033[35m Incorrect number of elements in offset list \033[0m')
            self.offset = self.new_list(0)
  
        

        # parameter init
        self.servo_positions = self.new_list(0)
        self.origin_positions = self.new_list(0)
        self.calibrate_position = self.new_list(0)
        self.direction = self.new_list(1)

        # servo init
        for i, pin in enumerate(pin_list):
            pwm = PWM(self.PINS[pin])
            servo = Servo(pwm)
            if None == init_angles:
                servo.angle(self.offset[i])
                self.servo_positions[i] = 0
            else:
                servo.angle(self.offset[i]+init_angles[i])
                self.servo_positions[i]=init_angles[i]
            self.servo_list.append(servo)
            time.sleep(0.1)

    def new_list(self, default_value):
        _ = [default_value] * self.pin_num
        return _

    def angle_list(self, angle_list):
        for i in range(self.pin_num):
            self.servo_list[i].angle(angle_list[i])

    def servo_write_all(self, angles):
        rel_angles = []  # ralative angle to home
        for i in range(self.pin_num):
            rel_angles.append(self.direction[i] * (self.origin_positions[i] + angles[i] + self.offset[i]))

        self.angle_list(rel_angles)

    def servo_move(self, targets, speed=50):
        '''
            calculate the max delta angle, multiply by 2 to define a max_step
            loop max_step times, every servo add/minus 1 when step reaches its adder_flag
        '''
        # sprint("Servo_move")
        speed = max(0, speed)
        speed = min(100, speed)
        delta = []
        absdelta = []
        max_step = 0
        steps = []

        for i in range(self.pin_num):
            value = targets[i] - self.servo_positions[i]
            delta.append(value)
            absdelta.append(abs(value))

        max_step = int(1*max(absdelta))
        if max_step != 0:
            for i in range(self.pin_num):
                step = float(delta[i])/max_step
                steps.append(step)

            for _ in range(max_step):
                for j in range(self.pin_num):
                    self.servo_positions[j] += steps[j]
                self.servo_write_all(self.servo_positions)
                #5~5005us
                t = (100-speed)*50+5
                time.sleep(t/100000)

    def do_action(self,motion_name, step=1, speed=50):
        for _ in range(step):
            for motion in self.move_list[motion_name]:
                self.servo_move(motion, speed)

    def set_offset(self,offset_list):
        offset_list = [ min(max(offset, -20), 20) for offset in offset_list]
        temp = str(offset_list)
        self.db.set(self.list_name,temp)
        self.offset = offset_list
        
    def calibration(self):
        self.servo_positions = self.calibrate_position
        self.servo_write_all(self.servo_positions)

    def reset(self,):
        self.servo_positions = self.new_list(0)
        self.servo_write_all(self.servo_positions)

    def soft_reset(self,):
        temp_list = self.new_list(0)
        self.servo_write_all(temp_list)
