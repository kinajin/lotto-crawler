const { sequelize } = require("./models");

// 데이터베이스 연결
async function connectDatabase() {
  try {
    await sequelize.authenticate();
    console.log("데이터베이스 연결 성공");

    //sequelize.sync() 메서드 호출은 정의된 모델을 바탕으로 데이터베이스에 테이블을 생성, 이미 테이블이 존재하는 경우에는 새로운 필드 등을 추가
    await sequelize.sync();
    console.log("데이터베이스 동기화 완료");
  } catch (error) {
    console.error("데이터베이스 연결 실패:", error);
  }
}

module.exports = {
  connectDatabase,
};
