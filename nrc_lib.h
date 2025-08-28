#ifndef NRC_LIB_H
#define NRC_LIB_H

//Accelus Robotics Robot Interface
#if	defined(_WIN32) || defined(WIN32)   //windows
#define EXPORT_API __declspec(dllexport)
#else
#define EXPORT_API
#endif

const int robotNum = 1;

enum servoStatus {
    stop = 0,
    ok = 1,
    error = 2,
    running = 3
};

struct MoveCmd {
    double pos[7];
    int coord;
    double velocity;
    double acc;
    double dec;
    int pl;
    int toolNum;
    int userNum;
};

struct toolParam {
    double X;                       //X
    double Y;                       //Y
    double Z;                       //Z
    double A;                       //A
    double B;                       //B
    double C;                       //C
    double payloadMass;             //
    double payloadInertia;          //
    double payloadMassCenter_X;     //
    double payloadMassCenter_Y;     //
    double payloadMassCenter_Z;     //
};

struct WaveParam {
    int type;                       //0 1 2 3
    double swingFreq;               //
    double swingAmplitude;          //
    double radius;                  //
    double LTypeAngle;              //
    bool moveWhenEdgeStay;          //
    double leftStayTime;            //
    double rightStayTime;           //
    int initialDir;                 //
    double horizontalDeflection;    //
    double verticalDeflection;      //
};

extern "C" {
EXPORT_API int connect_robot(const char* ip,const char* port,const char* robotName);
EXPORT_API int disconnect_robot(const char* robotName);
EXPORT_API int get_connection_status(const char* robotName);
EXPORT_API int clear_error(const char* robotName);
EXPORT_API int set_servo_state(int state,const char* robotName);
EXPORT_API int get_servo_state(const char* robotName);
EXPORT_API int set_servo_poweron(const char* robotName);
EXPORT_API int set_servo_poweroff(const char* robotName);
EXPORT_API int get_current_position(double* pos, int coord,const char* robotName);
EXPORT_API int get_robot_running_state(const char* robotName);
EXPORT_API int set_speed(int speed,const char* robotName);
EXPORT_API int get_speed(const char* robotName);
// Set the current coord tupe 0,1,2,3
EXPORT_API int set_current_coord(int coord,const char* robotName);
EXPORT_API int get_current_coord(const char* robotName);
// Set current mode 0,1,2
EXPORT_API int set_current_mode(int mode,const char* robotName);
EXPORT_API int get_current_mode(const char* robotName);
EXPORT_API int robot_start_jogging(int axis,bool dir,const char* robotName);
EXPORT_API int robot_stop_jogging(int axis,const char* robotName);
EXPORT_API int robot_go_to_reset_position(const char* robotName);
EXPORT_API int robot_go_home(const char* robotName);
EXPORT_API int robot_movej(double *pos,int vel,int coord,int acc, int dec,const char* robotName);
EXPORT_API int robot_movel(double *pos,int vel,int coord,int acc, int dec,const char* robotName);
EXPORT_API int job_stop(const char* robotName);
}

#endif // NRC_LIB_H
