package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/findPw")
public class FindPwServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        req.setCharacterEncoding("UTF-8");
        String userId = req.getParameter("user_id");
        String userName = req.getParameter("user_name");

        UserDAO dao = new UserDAO();
        boolean verified = dao.findUserPwByIdAndName(userId, userName);

        resp.setContentType("application/json; charset=UTF-8");
        if (verified) {
            resp.getWriter().write("{\"result\":\"success\"}");
        } else {
            resp.getWriter().write("{\"result\":\"fail\"}");
        }
    }
}