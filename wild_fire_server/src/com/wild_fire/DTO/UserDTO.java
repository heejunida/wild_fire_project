package com.wild_fire.DTO;

public class UserDTO {
    private String userName;
    private String userId;
    private String userPw;

    public UserDTO(String userName, String userId, String userPw) {
        this.userName = userName;
        this.userId = userId;
        this.userPw = userPw;
    }
    public UserDTO() {
    }
    public String getUserName() {
        return userName;
    }
    public void setUserName(String userName) {
        this.userName = userName;
    }
    public String getUserId() {
        return userId;
    }
    public void setUserId(String userId) {
        this.userId = userId;
    }
    public String getUserPw() {
        return userPw;
    }
    public void setUserPw(String userPw) {
        this.userPw = userPw;
    }
}
