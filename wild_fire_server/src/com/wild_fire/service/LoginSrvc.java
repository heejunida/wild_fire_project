package com.wild_fire.service;

import com.wild_fire.DAO.UserDAO;

public class LoginSrvc {

    private final UserDAO userDAO;

    public LoginSrvc() {
        this.userDAO = new UserDAO();
    }

    /**
     * 사용자의 아이디와 비밀번호를 인증하고, 성공 시 사용자의 고유 ID(u_id)를 반환합니다.
     * @param userId 사용자가 입력한 아이디
     * @param password 사용자가 입력한 비밀번호
     * @return 인증 성공 시 u_id, 실패 시 null
     */
    public Long authenticateAndGetUid(String userId, String password) {
        // UserDAO의 로그인 메소드를 직접 호출합니다.
        // DAO는 비밀번호 해싱(jBCrypt) 검증 로직을 포함하고 있어야 합니다.
        return userDAO.loginAndGetUid(userId, password);
    }
}